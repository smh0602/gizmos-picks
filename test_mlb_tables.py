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

from tcheck import ck, copy_module, eq, note, section  # noqa: E402

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
pdoc, odoc = M.build(REAL, through="2026-08-20", allow_incomplete=True)
pub = open(FIXTURE, encoding="utf-8").read().splitlines()
eq(len(pub), 185, "the published 8/20 fixture holds 185 rows")
eq(pdoc["rows"], 185, "the rebuilt 8/20 table has 185 rows at n >= 8")
eq(pdoc["sum_n"], 3403, "...and sum(n) = 3403")
mine = _psv_rows(M.render_pitchers_md(pdoc))
_miss = sorted(set(pub) - set(mine))
_extra = sorted(set(mine) - set(pub))
ck(not _miss and not _extra,
   "🔴 every published row reproduces BYTE FOR BYTE (185/185)",
   "missing %d, e.g. %s; extra %d, e.g. %s" % (len(_miss), _miss[:2], len(_extra), _extra[:2]))
_by = {r["name"]: r for r in pdoc["pitchers"]}
for _nm, _cvk, _cvo in (("Jacob Misiorowski", "0.252", "0.174"),
                        ("Logan Gilbert", "0.289", "0.132")):
    _r = _by.get(_nm)
    ck(_r is not None and M._f(_r["cvK"], 3) == _cvk and M._f(_r["cvO"], 3) == _cvo,
       "   acceptance: %s cvK %s / cvO %s" % (_nm, _cvk, _cvo),
       "got %s" % ((_r and (_r["cvK"], _r["cvO"])),))
ck(all(r["n"] >= 8 for r in pdoc["pitchers"]), "   no row under n = 8")

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
_B = json.load(gzip.open(os.path.join(ROOT, "data", "latest", "props.json.gz"), "rt"))
_fix = _B.get("pulled_at") or _B.get("written_at")
DRIVER = r'''
import datetime as _d, gzip, io, json, os, sys, contextlib
root = os.path.dirname(os.path.abspath(__file__)); os.chdir(root); sys.path.insert(0, root)
FIX = _d.datetime.strptime(%r, "%%Y-%%m-%%dT%%H:%%M:%%SZ").replace(
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
''' % _fix

TREE = os.path.join(TMP, "tree")
os.makedirs(os.path.join(TREE, "data"))
copy_module("card", TREE)
shutil.copytree(os.path.join(ROOT, "data", "latest"), os.path.join(TREE, "data", "latest"))
_day = _fix[:10]
for _sub in ("props-pitcher", "props-batter", "schedule"):
    _src = os.path.join(ROOT, "data", _day, _sub)
    if os.path.isdir(_src):
        shutil.copytree(_src, os.path.join(TREE, "data", _day, _sub))
open(os.path.join(TREE, "driver.py"), "w").write(DRIVER)
_PP = os.path.join(TREE, "data", "latest", "pitchers.json.gz")
_orig_bytes = open(_PP, "rb").read()


def drive(tag, players_json=None):
    if players_json is None:
        open(_PP, "wb").write(_orig_bytes)
    else:
        _dump(_PP, players_json)
    out = os.path.join(TMP, tag + ".json")
    p = subprocess.run([sys.executable, "-B", "driver.py", out], cwd=TREE,
                       capture_output=True, text=True, timeout=600,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    if p.returncode:
        print(p.stdout[-2000:], p.stderr[-2000:])
        return None
    return open(out, encoding="utf-8").read()


def salted(flag):
    """The real pull plus low-IP starters: a same-name same-team double for
    every board pitcher (would make `resolve()` refuse the join), one entry
    per name the board could not match (would newly join), and a heavy
    striker against every team (would move the centering constant)."""
    S = json.load(gzip.open(io.BytesIO(_orig_bytes), "rt"))
    S["starter_pool"] = "complete"
    extra, i = {}, 0

    def add(name, team, rows):
        nonlocal i
        i += 1
        e = {"name": name, "team": team, "throws": "R", "era": None, "whip": None,
             "w": 0, "l": 0, "gs": len(rows), "g": rows}
        if flag:
            e["below_min_ip"] = True
        extra["99%07d" % i] = e
    row = lambda d, o, k=12: {"d": d, "o": o, "h": 0, "gs": 1, "outs": 5, "k": k,
                              "er": 0, "hit": 1, "bb": 0, "np": 45, "bf": 8}
    for g in _B["games"]:
        for pr in g["props"]:
            if pr.get("kind") == "pitcher":
                add(pr["player"], pr.get("team"), [row("2026-06-01", g["away"])])
    for nm in _B.get("unmatched") or []:
        add(nm, _B["games"][0]["home"], [row("2026-06-02", _B["games"][0]["away"])])
    add("Heavy Striker", _teams[0], [row("2026-06-%02d" % (j % 28 + 1), t, 20)
                                      for j, t in enumerate(_teams)])
    S["players"].update(extra)
    S["n_below_min_ip"] = len(extra)
    return S, len(extra)


base = drive("base")
ck(base is not None, "the baseline board + card build in an isolated tree")
_bd = json.loads(base) if base else {}
_ncard = len(((_bd.get("card") or {}).get("picks")) or [])
_npit = sum(1 for r in ((_bd.get("card") or {}).get("picks") or []) if r.get("kind") != "hitter")
ck(_ncard > 0 and _npit > 0,
   "   ⚠️ the baseline card is NOT empty (%d picks, %d pitcher rows) — an empty "
   "card would make the comparison below pass blind" % (_ncard, _npit))
S1, _nx = salted(flag=True)
flagged = drive("flagged", S1)
ck(_nx >= 3, "   the salt adds %d below_min_ip starter(s)" % _nx)
ck(flagged is not None and flagged == base,
   "🔴🔴 board AND card are BYTE-IDENTICAL with the below_min_ip starters present",
   "the widening moved a model number")
S0, _ = salted(flag=False)
unflagged = drive("unflagged", S0)
ck(unflagged is not None and unflagged != base,
   "   positive control: the SAME salt unflagged DOES change them — so the "
   "identity above is the filter working, not an inert fixture")

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
