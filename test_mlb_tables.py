#!/usr/bin/env python3
"""THE MLB PITCHER + OPPONENT TABLES, REBUILT BY THE RUNNER — AND THE CARD
THAT MUST NOT NOTICE.

`mlb_tables.py` rebuilds both published tables from
`data/latest/pitchers.json.gz` right after the `pitchers` mode. To do that
the pull now carries EVERY starter, including those under the model's
20-IP bar (`below_min_ip`). Four things must hold:

  (a) the pitcher table reproduces the published 8/20 table, row for row
      (`research/mlb_pitcher_table_0820.psv`, 185 rows, sum(n) 3403) and
      the two acceptance pitchers;
  (b) the opponent table is internally whole: 30 teams, sum(n) is the
      population, the centering constant IS the population mean, the
      low-IP starters are IN it, and an incomplete pull is REFUSED;
  (c) 🔴🔴 THE CARD IS UNCHANGED BY THE POOL WIDENING. `card.py` and the
      props board read the model pool through `collect.model_pitchers()`;
      a pull salted with `below_min_ip` starters must build a
      byte-identical board and card. Driven, not asserted from source —
      and with a positive control proving the salt WOULD move them;
  (d) the tables module never writes into `picks/`.
Plus the collector itself, driven against a fake statsapi: the widened
pool, the flag, and the chain in `run_mode("pitchers")` that must never
lose the pull when a table fails.

⚠️ No network. The real artifact is read where one exists; everything
else is constructed.

# @vacuity (a) the pitcher table uses the SAMPLE SD, not the population SD
#   file: mlb_tables.py
#   find:         sK, sO = st.stdev(K), st.stdev(O)          # sample SD, n-1
#   with:         sK, sO = st.pstdev(K), st.pstdev(O)          # sample SD, n-1
#
# @vacuity (a) ...and publishes only n >= 8
#   file: mlb_tables.py
#   find: MIN_N = 8          # published only at n >= 8 (mlb-pitcher-database)
#   with: MIN_N = 7          # published only at n >= 8 (mlb-pitcher-database)
#
# @vacuity (a) ...and rounds HALF UP the way the published rows do
#   file: mlb_tables.py
#   find:     return decimal.Decimal(repr(x)).quantize(q, rounding=decimal.ROUND_HALF_UP)
#   with:     return decimal.Decimal(repr(x)).quantize(q, rounding=decimal.ROUND_HALF_EVEN)
#
# @vacuity (b) the centering constant is the population mean
#   file: mlb_tables.py
#   find:     C = sum(r["k"] for v in opp.values() for r in v) / N
#   with:     C = sum(r["k"] for v in opp.values() for r in v) / (N + 1)
#
# @vacuity (b) the low-IP starters are IN the table population
#   file: mlb_tables.py
#   find:         rows = [r for r in p.get("g") or []
#   with:         rows = [r for r in (p.get("g") if not p.get("below_min_ip") else []) or []
#
# @vacuity (b) an incomplete starter pool is refused
#   file: mlb_tables.py
#   find:     if pool != "complete" and not allow_incomplete:
#   with:     if False:
#
# @vacuity (c) 🔴🔴 the model pool excludes the below-min-IP starters
#   file: collect.py
#   find:     return {k: v for k, v in players.items() if not v.get("below_min_ip")}
#   with:     return dict(players)
#
# @vacuity (c1) the planted board is drawn from the model pool, so an empty pool leaves (c) red, never blind
#   file: collect.py
#   find:     return {k: v for k, v in players.items() if not v.get("below_min_ip")}
#   with:     return {}
#
# @vacuity (c) ...and card.py reads through that filter
#   file: card.py
#   find:     players = _c.model_pitchers(P["players"])
#   with:     players = P["players"]
#
# @vacuity (c) ...and so does the props board's join
#   file: collect.py
#   find:         for pid, v in model_pitchers(D["players"]).items():
#   with:         for pid, v in D["players"].items():
#
# @vacuity (d) the tables module refuses picks/
#   file: mlb_tables.py
#   find:     if "picks" in parts:
#   with:     if False:
#
# @vacuity the collector adds the starters under the bar, flagged
#   file: collect.py
#   find:                            "below_min_ip": True})
#   with:                            "below_min_ip": False})
#
# @vacuity the pitchers mode chains the tables
#   file: collect.py
#   find:                 _mt.write_all(LATEST)
#   with:                 pass
"""
import contextlib
import copy
import datetime
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, copy_module, eq, note, section, shown  # noqa: E402

import mlb_tables as M  # noqa: E402

REAL = os.path.join(ROOT, "data", "latest", "pitchers.json.gz")
FIXTURE = os.path.join(ROOT, "research", "mlb_pitcher_table_0820.psv")
TMP = tempfile.mkdtemp(prefix="mlbtab-")


def _dump(path, D):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(D, f)


def _real():
    return json.load(gzip.open(REAL, "rt", encoding="utf-8"))


def _psv_rows(md):
    return [l for l in md.splitlines()
            if l.count("|") == 10 and not l.startswith(("name|", "---"))]


# ══════════════════════════════════════════════════════════════════════
section("(a) THE PITCHER TABLE REPRODUCES THE PUBLISHED 8/20 TABLE")
# ⚠️ `allow_incomplete`: the n >= 8 rows cannot depend on starters under
# 20 IP, and the committed pull may predate the widening.
# 🔴 `[2026-09-28]` PINNED INPUT. This read `data/latest/pitchers.json.gz`,
#    the collector's ROLLING pull, rewritten for `now().year` on every
#    `pitchers` run — a frozen 2026-08-20 cutoff applied to a file that
#    follows the real calendar. The first 2027 pull would have left zero
#    starts through 8/20 and all of (a) red on correct code. ✅ (a) now
#    builds from `research/mlb_pitchers_0820.json.gz`: that pull trimmed,
#    once, to the 3,838 starts the 8/20 table is built from (gs == 1, dated
#    on or before 8/20), with only the fields mlb_tables reads — the same
#    table, byte for byte (measured when it was written). The live pull is
#    still reproduced as an EXTRA while it holds the 2026 season's 8/20.
PINNED = os.path.join(ROOT, "research", "mlb_pitchers_0820.json.gz")
pub = open(FIXTURE, encoding="utf-8").read().splitlines()
eq(len(pub), 185, "the published 8/20 fixture holds 185 rows")


def _reproduces(path, who):
    pdoc, _o = M.build(path, through="2026-08-20", allow_incomplete=True)
    eq(pdoc["rows"], 185, "%s: the rebuilt 8/20 table has 185 rows at n >= 8" % who)
    eq(pdoc["sum_n"], 3403, "%s: ...and sum(n) = 3403" % who)
    mine = _psv_rows(M.render_pitchers_md(pdoc))
    miss = sorted(set(pub) - set(mine))
    extra = sorted(set(mine) - set(pub))
    ck(not miss and not extra,
       "🔴 %s: every published row reproduces BYTE FOR BYTE (185/185)" % who,
       "missing %d, e.g. %s; extra %d, e.g. %s" % (len(miss), miss[:2], len(extra), extra[:2]))
    by = {r["name"]: r for r in pdoc["pitchers"]}
    for nm, cvk, cvo in (("Jacob Misiorowski", "0.252", "0.174"),
                         ("Logan Gilbert", "0.289", "0.132")):
        r = by.get(nm)
        ck(r is not None and M._f(r["cvK"], 3) == cvk and M._f(r["cvO"], 3) == cvo,
           "   %s acceptance: %s cvK %s / cvO %s" % (who, nm, cvk, cvo),
           "got %s" % ((r and (r["cvK"], r["cvO"])),))
    ck(all(r["n"] >= 8 for r in pdoc["pitchers"]), "   %s: no row under n = 8" % who)


_reproduces(PINNED, "PINNED")
_real0 = _real()
_live_820 = [r for p in _real0["players"].values() for r in p.get("g") or []
             if r.get("gs") == 1 and "2026-03-01" <= (r.get("d") or "") <= "2026-08-20"]
if str(_real0.get("pulled_at", ""))[:4] == "2026" and _live_820:
    _reproduces(REAL, "LIVE PULL")
else:
    note("⚪ the live pull no longer holds the 2026 season through 8/20 "
         "(pulled %s, %d such starts); the pinned pull above asked (a)"
         % (_real0.get("pulled_at"), len(_live_820)))

# ══════════════════════════════════════════════════════════════════════
section("(b) THE OPPONENT TABLE IS WHOLE, AND ITS POPULATION IS EVERY STARTER")
D = _real()
_thr = M.latest_completed_slate(D["pulled_at"])
pd2, od2 = M.build(REAL, allow_incomplete=True)
eq(od2["through"], _thr, "through = the latest COMPLETED slate of the pull")
eq(M.latest_completed_slate("2026-09-21T10:02:56Z"), "2026-09-20",
   "   a 06:00 ET pull -> last night")
eq(M.latest_completed_slate("2026-09-22T02:30:00Z"), "2026-09-20",
   "   a 22:30 ET re-pull mid-slate -> still last night, not the half slate")
eq(od2["rows"], 30, "30 teams")
_codes = {r["team"] for r in od2["opponents"]}
ck("AZ" in _codes and len(_codes) == 30 and _codes <= set(__import__("card").ABBR.values()),
   "   every team is a card.py code (Arizona = AZ)", str(sorted(_codes)))
eq(sum(r["n"] for r in od2["opponents"]), od2["population_starts"],
   "sum(n) == population_starts")
# independent recompute, straight off the raw file
_K = [r["k"] for p in D["players"].values() for r in p["g"]
      if r.get("gs") == 1 and r["d"] <= od2["through"]]
eq(od2["population_starts"], len(_K), "   population = every start in the file through `through`")
ck(abs(od2["centering_constant"] - round(sum(_K) / len(_K), 4)) < 1e-9,
   "🔴 the centering constant IS the population's mean K",
   "%s vs %s" % (od2["centering_constant"], sum(_K) / len(_K)))
import card as _card  # noqa: E402
eq(od2["slope"], _card.K_OPP_B, "ΔE[K] slope is card.py's K_OPP_B, not a restated copy")
ck(all(abs(r["dEK"] - (r["meanK"] - sum(_K) / len(_K)) * _card.K_OPP_B) < 1e-9
       for r in od2["opponents"]), "   every ΔE[K] = (meanK − C) × slope")
for _k in ("through", "population_starts", "centering_constant", "source_pulled_at", "built_at"):
    ck(_k in pd2 and _k in od2, "   both docs carry `%s`" % _k)

# the low-IP starters are counted, and an incomplete pull is refused
_W = copy.deepcopy(D)
_W["starter_pool"] = "complete"
_teams = sorted({r["o"] for p in D["players"].values() for r in p["g"] if r.get("o")})
_W["players"]["999000001"] = {
    "name": "Low Ip Starter", "team": _teams[0], "throws": "R", "below_min_ip": True,
    "gs": 3, "g": [{"d": "2026-05-0%d" % (i + 1), "o": _teams[i + 1], "h": 1, "gs": 1,
                    "outs": 6, "k": 9, "np": 40} for i in range(3)]}
_wp = os.path.join(TMP, "widened.json.gz")
_dump(_wp, _W)
_, _ow = M.build(_wp, through=od2["through"])
eq(_ow["population_starts"], od2["population_starts"] + 3,
   "🔴 a below_min_ip starter's 3 starts ARE in the population")
ck(_ow["population_complete"] is True, "   ...and a complete pull says so")
_ip = os.path.join(TMP, "incomplete.json.gz")
_I = copy.deepcopy(_W)
_I["starter_pool"] = "FAILED: URLError: test"
_dump(_ip, _I)
try:
    M.build(_ip)
    _refused = False
except RuntimeError:
    _refused = True
ck(_refused, "🔴 an incomplete starter pool is REFUSED, not published under a full label")
if D.get("starter_pool") == "complete":
    _, _o820 = M.build(REAL, through="2026-08-20")
    note("8/20 opponent population from the widened pull: %d starts, C %.4f "
         "(published: 3838, 4.7376)" % (_o820["population_starts"], _o820["centering_constant"]))
else:
    note("⚠️ the committed pull predates the widening (starter_pool=%r): the 8/20 "
         "opponent acceptance (3838 starts, C 4.7376) is NOT YET MEASURABLE here"
         % D.get("starter_pool"))

# ══════════════════════════════════════════════════════════════════════
section("(c) 🔴🔴 THE CARD AND THE BOARD ARE UNCHANGED BY THE WIDENING")
# 🔴 `[2026-09-28]` THE CASE IS PLANTED, NOT BORROWED FROM TODAY'S BOARD.
#    This section drove the LIVE props board, so its rule-67 case — priced
#    pitcher props on the card — existed only while production had them:
#    an MLB off-day, the All-Star break or the whole offseason leaves the
#    newest pitcher snapshot empty, and then "the card carries pitcher
#    model output", "the salt adds >= 3 starters" and the positive control
#    were all red on correct code (and the identity check proved nothing).
#    ✅ (c1) now plants the board: a pitcher-props snapshot for three games
#    between six starters drawn from the pull itself (the most-started arm
#    of six different teams, every name unique in the model pool), two
#    books, both markets, and the clock pinned just after it. It always has
#    pitchers to price, to double and to perturb.
#    ➡️ (c2), today's live board, runs as an EXTRA when it holds >= 3
#    pitcher props, and is reported otherwise.
DRIVER = r"""
import datetime as _d, gzip, io, json, os, sys, contextlib
root = os.path.dirname(os.path.abspath(__file__)); os.chdir(root); sys.path.insert(0, root)
FIX = _d.datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%SZ").replace(
    tzinfo=_d.timezone.utc) + _d.timedelta(minutes=2)
import collect, card
collect.now = lambda: FIX
class _DT(_d.datetime):
    @classmethod
    def now(cls, tz=None):
        return FIX if tz else FIX.replace(tzinfo=None)
card.datetime = _DT
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    collect.collect_props_board()
    doc = card.main(dry=True)
board = json.load(gzip.open("data/latest/props.json.gz", "rt"))
json.dump({"board": board, "card": doc}, open(sys.argv[1], "w"), sort_keys=True)
"""


def c_tree(tag, day_dirs=()):
    """An isolated tree: card + its imports, a copy of data/latest, and
    whichever day directories the caller names."""
    tree = os.path.join(TMP, tag)
    os.makedirs(os.path.join(tree, "data"))
    copy_module("card", tree)
    shutil.copytree(os.path.join(ROOT, "data", "latest"), os.path.join(tree, "data", "latest"))
    for day, sub in day_dirs:
        src = os.path.join(ROOT, "data", day, sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(tree, "data", day, sub))
    open(os.path.join(tree, "driver.py"), "w").write(DRIVER)
    return tree


def c_drive(tree, fix, orig, tag, players_json=None):
    pp = os.path.join(tree, "data", "latest", "pitchers.json.gz")
    if players_json is None:
        open(pp, "wb").write(orig)
    else:
        _dump(pp, players_json)
    out = os.path.join(TMP, tag + ".json")
    p = subprocess.run([sys.executable, "-B", "driver.py", out, fix], cwd=tree,
                       capture_output=True, text=True, timeout=600,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    if p.returncode:
        print(shown(p.stdout[-2000:]), shown(p.stderr[-2000:]))
        return None
    return open(out, encoding="utf-8").read()


def salted(orig, board, flag, day0):
    """The pull plus low-IP starters: a same-name same-team double for
    every board pitcher (would make `resolve()` refuse the join), one entry
    per name the board could not match (would newly join), and a heavy
    striker against every team (would move the centering constant).
    ⚠️ `[2026-10-09]` Their starts are dated from `day0`, before the first
    scored day: the MLB game model (on the card since #235) folds EVERY start
    of every scored day into its league starter averages by design, so the
    heavy striker's 30 made-up June starts moved the live card's moneyline,
    Cleveland 56 -> 55 (78065e9), and collect went red 10-08 -> 10-09. Before
    any scored day they still reach the prop model (it reads every start
    before today) and never the game model's ledger."""
    S = json.load(gzip.open(io.BytesIO(orig), "rt"))
    S["starter_pool"] = "complete"
    teams = sorted({r["o"] for q in S["players"].values() for r in q.get("g") or []
                    if r.get("o")})
    extra, i = {}, 0

    def add(name, team, rows):
        nonlocal i
        i += 1
        e = {"name": name, "team": team, "throws": "R", "era": None, "whip": None,
             "w": 0, "l": 0, "gs": len(rows), "g": rows}
        if flag:
            e["below_min_ip"] = True
        extra["99%07d" % i] = e
    row = lambda j, o, k=12: {"d": (day0 + datetime.timedelta(days=j)).isoformat(), "o": o,
                              "h": 0, "gs": 1, "outs": 5, "k": k,
                              "er": 0, "hit": 1, "bb": 0, "np": 45, "bf": 8}
    games = board.get("games") or []
    for g in games:
        for pr in g["props"]:
            if pr.get("kind") == "pitcher":
                add(pr["player"], pr.get("team"), [row(0, g["away"])])
    for nm in (board.get("unmatched") or []) if games else []:
        add(nm, games[0]["home"], [row(1, games[0]["away"])])
    add("Heavy Striker", teams[0], [row(j % 28, t, 20) for j, t in enumerate(teams)])
    S["players"].update(extra)
    S["n_below_min_ip"] = len(extra)
    return S, len(extra)


def c_run(who, tree, fix):
    """Base, flagged and unflagged drives, and the four checks, on one tree."""
    orig = open(os.path.join(tree, "data", "latest", "pitchers.json.gz"), "rb").read()
    base = c_drive(tree, fix, orig, who + "-base")
    ck(base is not None, "%s: the baseline board + card build in an isolated tree" % who)
    bd = json.loads(base) if base else {}
    cd = bd.get("card") or {}
    ncard = len(cd.get("picks") or [])
    npit = sum(1 for r in (cd.get("picks") or []) if r.get("kind") != "hitter")
    # 🔴 `[2026-09-25]` ~~pitcher rows on the BOARD~~ asked the wrong question
    #    once C2 shipped (research/mlb_pitcher_cal_spec.md): a corrected pitcher
    #    number rarely beats its price, so a correct card can put NO pitcher on
    #    the board (the 2026-09-25 replay: 50 picks, 0 pitcher rows) and this
    #    guard failed a correct card. ✅ What makes the comparison below
    #    non-blind is PITCHER MODEL OUTPUT anywhere on the card: every priced
    #    pitcher prop's projection (hundreds, board or not) and the pitcher
    #    pairs. It must still be there.
    npj = sum(1 for k in (cd.get("projections") or {})
              if k.split("|")[1:2] in (["pitcher_strikeouts"], ["pitcher_outs"]))
    npair = len(cd.get("pairs") or [])
    ck(ncard > 0 and npj > 0,
       "   ⚠️ %s: the baseline card carries pitcher model output (%d picks, %d "
       "pitcher rows on the board, %d pitcher projections, %d pairs) — a card "
       "without it would make the comparison below pass blind"
       % (who, ncard, npit, npj, npair))
    sp = os.path.join(tree, "data", "latest", "scores.json.gz")
    scored = (json.load(gzip.open(sp, "rt")).get("days") or {}) if os.path.exists(sp) else {}
    day0 = datetime.date.fromisoformat(min(scored) if scored else "2026-03-01") - datetime.timedelta(days=30)
    s1, nx = salted(orig, bd.get("board") or {}, flag=True, day0=day0)
    flagged = c_drive(tree, fix, orig, who + "-flagged", s1)
    ck(nx >= 3, "   %s: the salt adds %d below_min_ip starter(s)" % (who, nx))
    ck(flagged is not None and flagged == base,
       "🔴🔴 %s: board AND card are BYTE-IDENTICAL with the below_min_ip starters "
       "present" % who, "the widening moved a model number")
    s0, _ = salted(orig, bd.get("board") or {}, flag=False, day0=day0)
    unflagged = c_drive(tree, fix, orig, who + "-unflagged", s0)
    ck(unflagged is not None and unflagged != base,
       "   %s: positive control: the SAME salt unflagged DOES change them — so "
       "the identity above is the filter working, not an inert fixture" % who)
    open(os.path.join(tree, "data", "latest", "pitchers.json.gz"), "wb").write(orig)


# ── (c1) PLANTED ──────────────────────────────────────────────────────
_PT = c_tree("tree-planted")
_PD = json.load(gzip.open(os.path.join(_PT, "data", "latest", "pitchers.json.gz"), "rt"))
import collect as _CM  # noqa: E402
_mp = _CM.model_pitchers(_PD["players"])
_nm_count = {}
for _v in _mp.values():
    _k = _CM.norm_name(_v["name"])
    _nm_count[_k] = _nm_count.get(_k, 0) + 1
_by_team = {}
for _pid, _v in sorted(_mp.items(), key=lambda kv: (-sum(1 for r in kv[1].get("g") or []
                                                       if r.get("gs")), kv[0])):
    _st = sum(1 for r in _v.get("g") or [] if r.get("gs"))
    if (_st >= 5 and _v.get("team") and _v["team"] not in _by_team
            and _nm_count[_CM.norm_name(_v["name"])] == 1):
        _by_team[_v["team"]] = _v
_six = list(_by_team.values())[:6]
_pull_at = datetime.datetime.strptime(_PD["pulled_at"], "%Y-%m-%dT%H:%M:%SZ")
_pfix = (_pull_at + datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
_ko = (_pull_at + datetime.timedelta(days=1)).strftime("%Y-%m-%dT23:05:00Z")


def _mkt(key, who, line, over, under):
    return {"key": key, "outcomes": [
        {"name": "Over", "description": who, "point": line, "price": over},
        {"name": "Under", "description": who, "point": line, "price": under}]}


_events = []
for _gi in range(len(_six) // 2):
    _aw, _hm = _six[2 * _gi], _six[2 * _gi + 1]
    _events.append({"id": "planted-%d" % _gi, "commence_time": _ko,
                    "away_team": _aw["team"], "home_team": _hm["team"],
                    "bookmakers": [
                        {"key": bk, "markets": [
                            m for q in (_aw, _hm) for m in (
                                _mkt("pitcher_strikeouts", q["name"], 5.5, -115 + dx, -105 - dx),
                                _mkt("pitcher_outs", q["name"], 16.5, -110 + dx, -110 - dx))]}
                        for bk, dx in (("draftkings", 0), ("fanduel", 5))]})
_snapdir = os.path.join(_PT, "data", _pfix[:10], "props-pitcher")
os.makedirs(_snapdir)
with gzip.open(os.path.join(_snapdir, _pfix[11:13] + _pfix[14:16] + ".json.gz"), "wt") as _fh:
    json.dump({"pulled_at": _pfix, "n_events": len(_events), "events": _events}, _fh)
ck(len(_events) == 3,
   "⚠️ PLANTED: three games between six starters from six different teams "
   "(%s)" % [q["name"] for q in _six])
c_run("PLANTED", _PT, _pfix)

# ── (c2) THE LIVE BOARD — the extra ───────────────────────────────────
_B = json.load(gzip.open(os.path.join(ROOT, "data", "latest", "props.json.gz"), "rt"))
_live_pp = sum(1 for g in _B.get("games") or [] for pr in g.get("props") or []
               if pr.get("kind") == "pitcher")
# ⚠️ THE CLOCK IS THE NEWEST STORED PITCHER SNAPSHOT, not the board's stamp
#    `[2026-09-29]`: a board rebuilt after 00:00Z carries today's date while
#    its pitcher props were priced from yesterday's snapshot, and a build at
#    the board's clock finds "no prop snapshots stored" for today -- the
#    extra ran without its case. Gated on that snapshot existing.
import glob as _glob  # noqa: E402
_snaps = sorted(_glob.glob(os.path.join(ROOT, "data", "20*", "props-pitcher", "*.json.gz")))
_fix = (json.load(gzip.open(_snaps[-1], "rt")).get("pulled_at") if _snaps else None)
if _fix and _live_pp >= 3:
    _day = _fix[:10]
    c_run("LIVE", c_tree("tree-live", [(_day, s) for s in
                                       ("props-pitcher", "props-batter", "schedule")]),
          _fix)
else:
    note("⚪ LIVE EXTRA NOT RUN: today's MLB board holds %d pitcher prop(s); the "
         "planted board above asked (c)" % _live_pp)

# ══════════════════════════════════════════════════════════════════════
section("(d) THE TABLES MODULE NEVER WRITES INTO picks/")
_lat = os.path.join(TMP, "w", "data", "latest")
os.makedirs(_lat)
shutil.copy(_wp, os.path.join(_lat, "pitchers.json.gz"))
with contextlib.redirect_stdout(io.StringIO()):
    M.write_all(_lat)
eq(sorted(os.listdir(_lat)), sorted(("pitchers.json.gz",) + M.ARTIFACTS),
   "write_all writes exactly its four artifacts, beside the pull")
_pk = os.path.join(TMP, "w", "picks")
os.makedirs(_pk)
shutil.copy(_wp, os.path.join(_pk, "pitchers.json.gz"))
try:
    with contextlib.redirect_stdout(io.StringIO()):
        M.write_all(_pk)
    _blocked = False
except ValueError:
    _blocked = True
ck(_blocked and os.listdir(_pk) == ["pitchers.json.gz"],
   "🔴 a picks/ destination is refused and nothing is written there")
for _a in ("pitcher-table.json", "opponent-table.json"):
    _j = json.load(open(os.path.join(_lat, _a)))
    ck(_j.get("built_at") and _j.get("label") == "DESCRIPTIVE",
       "   %s is stamped (`built_at`) and labelled DESCRIPTIVE" % _a)

# ══════════════════════════════════════════════════════════════════════
section("THE COLLECTOR: THE WIDENED POOL, THE FLAG, AND THE CHAIN")
import collect as C  # noqa: E402


def fake_statsapi(fail_pool2=False):
    ppl = {
        1: ("Model Arm", "R", 90, 5, 3),        # >= 20 IP: pool 1
        2: ("Spot Starter", "L", 30, 2, 2),     # starter under 20 IP: pool 2 adds
        3: ("Pure Reliever", "R", 15, 0, 0),    # never started: nobody adds
    }

    def ip(o):
        return "%d.%d" % (o // 3, o % 3)

    def get(url, timeout=30):
        if "stats?stats=season" in url:
            if "playerPool=All" in url:
                if fail_pool2:
                    raise OSError("pool 2 down")
                ids = (1, 2, 3)
            else:
                ids = tuple(i for i in (1, 2, 3) if ppl[i][2] >= 60)
            return {"stats": [{"splits": [
                {"player": {"id": i, "fullName": ppl[i][0]}, "team": {"name": "Team %d" % i},
                 "stat": {"inningsPitched": ip(ppl[i][2]), "gamesStarted": ppl[i][3],
                          "era": "3.00", "whip": "1.1", "wins": 1, "losses": 1}}
                for i in ids]}]}, {}
        if "/people?personIds=" in url:
            ids = [int(x) for x in url.split("personIds=")[1].split("&")[0].split(",")]
            return {"people": [{"id": i, "pitchHand": {"code": ppl[i][1]}} for i in ids]}, {}
        pid = int(url.split("/people/")[1].split("/")[0])
        n = ppl[pid][4] or 2
        return {"stats": [{"splits": [
            {"date": "2026-05-%02d" % (j + 1), "isHome": True,
             "opponent": {"name": "Opp %d" % j},
             "stat": {"gamesStarted": 1 if ppl[pid][4] else 0,
                      "inningsPitched": ip(ppl[pid][2] // n), "strikeOuts": 4,
                      "earnedRuns": 1, "hits": 3, "baseOnBalls": 1,
                      "numberOfPitches": 80, "battersFaced": 20}}
            for j in range(n)]}]}, {}
    return get


_cl = os.path.join(TMP, "c", "latest")
os.makedirs(_cl)
_saved = (C.get, C.LATEST)
try:
    C.get, C.LATEST = fake_statsapi(), _cl
    with contextlib.redirect_stdout(io.StringIO()):
        C.collect_pitchers()
    P = json.load(gzip.open(os.path.join(_cl, "pitchers.json.gz"), "rt"))
    eq(sorted(P["players"]), ["1", "2"], "pool 1 + the starter under the bar; the reliever is not added")
    ck(P["players"]["2"].get("below_min_ip") is True and "below_min_ip" not in P["players"]["1"],
       "🔴 the added starter is flagged below_min_ip, the model arm is not")
    eq(sorted(C.model_pitchers(P["players"])), ["1"], "   model_pitchers() is the 20-IP pool")
    eq((P["n_players"], P["n_below_min_ip"], P["starter_pool"]), (1, 1, "complete"),
       "   n_players keeps its meaning (model pool); the pool says complete")

    C.get = fake_statsapi(fail_pool2=True)
    with contextlib.redirect_stdout(io.StringIO()):
        C.collect_pitchers()
    P = json.load(gzip.open(os.path.join(_cl, "pitchers.json.gz"), "rt"))
    ck(sorted(P["players"]) == ["1"] and P["starter_pool"].startswith("FAILED"),
       "   a failed starter pool keeps the model pull and SAYS it failed", P["starter_pool"])

    # the chain: run_mode("pitchers") writes the tables...
    C.get = fake_statsapi()
    for f in M.ARTIFACTS:
        if os.path.exists(os.path.join(_cl, f)):
            os.remove(os.path.join(_cl, f))
    with contextlib.redirect_stdout(io.StringIO()):
        C.run_mode("pitchers")
    ck(all(os.path.exists(os.path.join(_cl, f)) for f in M.ARTIFACTS),
       "🔴 run_mode('pitchers') chains the tables: all four artifacts written")
    # ...and a table failure cannot lose the pull
    for f in M.ARTIFACTS:
        os.remove(os.path.join(_cl, f))
    os.remove(os.path.join(_cl, "pitchers.json.gz"))
    _wa = M.write_all
    M.write_all = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("table boom"))
    _buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(_buf):
            C.run_mode("pitchers")
        _raised = False
    except Exception:
        _raised = True
    finally:
        M.write_all = _wa
    ck(not _raised and os.path.exists(os.path.join(_cl, "pitchers.json.gz")),
       "🔴 a table failure does NOT lose the pitchers pull")
    ck("MLB TABLES FAILED" in _buf.getvalue(), "   ...and it is LOUD in the log")
finally:
    C.get, C.LATEST = _saved

shutil.rmtree(TMP, ignore_errors=True)
