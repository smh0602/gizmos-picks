#!/usr/bin/env python3
"""🔴 A STAMP-ONLY REWRITE OF A GZIP IS A HEARTBEAT, NOT A COPY — AND THE
HEARTBEAT IS MOVED, NEVER DROPPED. `[2026-10-28]`

The defect: `collect.write` rewrote a gzip whose content had not changed,
because its stamps moved. Git cannot delta a gzip, so every such rewrite
was a whole copy kept for ever: pitchers.json.gz + hitters.json.gz were the
same content from 2026-10-01 to 10-27 and stored ~590 KB a day.

The trap beside it (nfl.py, 2026-10-26): the rewrite IS the outage alarm.
A skip that drops the stamp leaves the row stale on a healthy day (a red
run), and the first fix of that kind hid a 10-day nflverse outage. So:

  §1  write(heartbeat=True) keeps the gzip's bytes and writes the heartbeat;
      the document every reader sees is EXACTLY the full write's.
  §2  the heartbeat is bound to the file's exact bytes: anything else that
      touches the file voids it (stale, never falsely fresh).
  §3  the contract: a stamp-only pull keeps the row fresh, a failed pull
      leaves it stale at the same deadline as before.
  §4  the CLASS: every scope that names a heartbeat file and reads a stamp
      reads it through freshness; every gzip `write` in collect.py decides.
  §5  the real chain: two identical pitcher pulls, then the tables.

⛔ A TEST ASKS THE CODE: every tree here is planted, every clock pinned.

# @vacuity 🔴 a skip that DROPS the heartbeat (nfl.py's 10-day lesson) is caught
#   file: freshness.py
#   find:         os.replace(tmp, hp)
#   with:         pass
#
# @vacuity 🔴 a heartbeat that is not bound to the file's bytes is caught
#   file: freshness.py
#   find:     if b.get("sha256") != hashlib.sha256(buf).hexdigest():
#   with:     if False:
#
# @vacuity 🔴 a doc that gains or loses a stamp field is a content change
#   file: freshness.py
#   find:     if not isinstance(stored, dict) or set(_stamps(stored)) != set(st):
#   with:     if not isinstance(stored, dict):
#
# @vacuity 🔴 int player ids are compared as JSON stores them (no false change)
#   file: freshness.py
#   find:         new = json.loads(json.dumps(doc))          # int keys -> str, as stored
#   with:         new = doc
#
# @vacuity 🔴 stamp_of reads through the heartbeat (the contract sees the pull's own time)
#   file: freshness.py
#   find:     doc = with_heartbeat(path, _load(path))
#   with:     doc = _load(path)
#
# @vacuity 🔴 the card's loader reads through the heartbeat (the census sees its callers)
#   file: card.py
#   find:     return _F.with_heartbeat(path, doc)   # a stamp-only pull's stamps (freshness)
#   with:     return doc
#
# @vacuity 🔴 a page read of a heartbeat file's stamp is caught
#   file: index.html
#   find:     <p><span class="rec">built ${R.built_at}</span></p>
#   with:     <p><span class="rec">built ${RECDETAIL.built_at}</span></p>
#
# @vacuity 🔴 a skip of a CHANGED document is caught
#   file: collect.py
#   find:         if _fresh.keep_with_heartbeat(path, obj):
#   with:         if _fresh.keep_with_heartbeat(path, obj) or os.path.exists(path):
#
# @vacuity ⚠️ a full write clears the heartbeat it supersedes
#   file: collect.py
#   find:     _fresh.drop_heartbeat(path)            # the file now carries its own stamps
#   with:     pass
#
# @vacuity 🔴 the pitchers pull that stopped passing heartbeat=True is caught
#   file: collect.py
#   find:         "players": logs}, compress=True, heartbeat=True)
#   with:         "players": logs}, compress=True)
#
# @vacuity 🔴 a reader of the pull's own stamp that skips the overlay is caught
#   file: mlb_tables.py
#   find:     D = _F.with_heartbeat(path, json.load(gzip.open(path, "rt", encoding="utf-8")))
#   with:     D = json.load(gzip.open(path, "rt", encoding="utf-8"))
#
# @vacuity 🔴 a test tree copied with its heartbeats unsettled is caught
#   file: tcheck.py
#   find:         if isinstance(doc, dict) and live != doc:
#   with:         if False:
#
# @vacuity 🔴 ...and a test that copies latest/ around copy_latest is caught
#   file: test_mlb_tables.py
#   find:     copy_latest(os.path.join(ROOT, "data", "latest"), os.path.join(tree, "data", "latest"))
#   with:     shutil.copytree(os.path.join(ROOT, "data", "latest"), os.path.join(tree, "data", "latest"))
"""
import ast
import contextlib
import datetime
import glob
import gzip
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)    # other files' escapes, parsed not run
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, eq, note, section  # noqa: E402

import collect as C  # noqa: E402
import freshness as F  # noqa: E402
import mlb_tables as M  # noqa: E402

UTC = datetime.timezone.utc
TMP = tempfile.mkdtemp(prefix="heartbeat-")


def at(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


@contextlib.contextmanager
def clock(s, latest=None, get=None):
    """collect's clock (and LATEST / get) pinned; collect's log silenced."""
    saved = (C.now, C.LATEST, C.get)
    C.now = lambda: at(s)
    if latest:
        C.LATEST = latest
    if get:
        C.get = get
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            yield
    finally:
        C.now, C.LATEST, C.get = saved


def raw(p):
    return json.load(gzip.open(p, "rt", encoding="utf-8"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ══════════════════════════════════════════════════════════════════════
section("1. write(heartbeat=True): THE BYTES STAY, THE DOCUMENT IS THE FULL WRITE'S")
# ══════════════════════════════════════════════════════════════════════
A, B = os.path.join(TMP, "a"), os.path.join(TMP, "b")
os.makedirs(A)
os.makedirs(B)
pa, pb = os.path.join(A, "logs.json.gz"), os.path.join(B, "logs.json.gz")
DOC = {"season": 2026, "players": {7: {"name": "Arm", "g": [{"d": "2026-09-27", "k": 6}]}}}

with clock("2026-11-09T10:16:00Z"):
    C.write(pa, dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
first = sha(pa)
ck(not os.path.exists(F.heartbeat_path(pa)), "a first write is a full write (no heartbeat)")

with clock("2026-11-10T10:16:30Z"):
    C.write(pa, dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
    C.write(pb, dict(DOC, pulled_at=C.stamp()), compress=True)        # the old way
eq(sha(pa), first, "🔴 a stamp-only pull leaves the gzip's BYTES as they were")
ck(os.path.exists(F.heartbeat_path(pa)), "   ...and writes the heartbeat beside it")
ck(F.heartbeat_path(pa).endswith(".json.gz.beat.json") and not F.heartbeat_path(pa).endswith(".gz"),
   "   the heartbeat is plain JSON and never matches a `*.json.gz` glob")
eq(F.with_heartbeat(pa, raw(pa)), raw(pb),
   "🔴🔴 the document a reader sees IS the one the full write stored, stamps included")
eq(F.stamp_of(pa), at("2026-11-10T10:16:30Z"), "🔴 stamp_of reads the new pull's pulled_at")
eq(F.stamp_of(pa), F.stamp_of(pb), "   ...exactly as it reads the fully rewritten file")
eq(raw(pa)["pulled_at"], "2026-11-09T10:16:00Z", "   (the gzip itself still says yesterday)")
eq(F.stamp_of(F.heartbeat_path(pa)), at("2026-11-10T10:16:30Z"),
   "   the heartbeat carries its own written_at (it is never a stampless file)")
ck(os.path.exists(F.heartbeat_path(pa)) and os.path.getsize(F.heartbeat_path(pa)) < 1000,
   "   it is a few hundred bytes of text")

with clock("2026-11-11T10:16:00Z"):
    C.write(pa, dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
eq((sha(pa), F.stamp_of(pa)), (first, at("2026-11-11T10:16:00Z")),
   "   a second stamp-only day: same bytes, the heartbeat moves on")

_changed = dict(DOC, players={7: {"name": "Arm", "g": [{"d": "2026-09-27", "k": 7}]}})
with clock("2026-11-12T10:16:00Z"):
    C.write(pa, dict(_changed, pulled_at=C.stamp()), compress=True, heartbeat=True)
ck(sha(pa) != first and raw(pa)["players"]["7"]["g"][0]["k"] == 7,
   "🔴 a CORRECTED game (statsapi did this on 09-29 and 10-01) is a full write")
ck(not os.path.exists(F.heartbeat_path(pa)), "   ...and the full write clears the heartbeat")
eq(F.stamp_of(pa), at("2026-11-12T10:16:00Z"), "   ...and the file's own stamp is read again")

_before = sha(pa)
with clock("2026-11-13T10:16:00Z"):
    C.write(pa, dict(_changed, pulled_at=C.stamp(), built_at=C.stamp()), compress=True,
            heartbeat=True)
ck(sha(pa) != _before, "🔴 a document that GAINS a stamp field is a content change, written")

with clock("2026-11-14T10:16:00Z"):
    C.write(pa, {"season": 2026, "players": {"7": {"name": "Arm", "g": []}}, "pulled_at": C.stamp()},
            compress=True)
    _b = sha(pa)
    C.write(pa, {"season": 2026, "players": {7: {"name": "Arm", "g": []}}, "pulled_at": C.stamp()},
            compress=True, heartbeat=True)
eq(sha(pa), _b, "   int player ids compare as the strings JSON stores (no false change)")

_bad = os.path.join(A, "bad.json.gz")
open(_bad, "wb").write(b"not a gzip")
with clock("2026-11-14T10:17:00Z"):
    C.write(_bad, {"x": 1}, compress=True, heartbeat=True)
eq(raw(_bad), {"x": 1, "written_at": "2026-11-14T10:17:00Z"}, "   an unreadable stored file is rewritten")
try:
    with clock("2026-11-14T10:17:00Z"):
        C.write(os.path.join(A, "plain.json"), {"x": 1}, heartbeat=True)
    _raised = False
except ValueError:
    _raised = True
ck(_raised, "   heartbeat=True on a plain file is refused (git deltas text; a CRLF checkout "
            "would void its byte binding)")

# ══════════════════════════════════════════════════════════════════════
section("2. BOUND TO THE EXACT BYTES: ANYTHING ELSE VOIDS IT (STALE, NEVER FALSELY FRESH)")
# ══════════════════════════════════════════════════════════════════════
D2 = os.path.join(TMP, "bind")
os.makedirs(D2)
p2 = os.path.join(D2, "logs.json.gz")
with clock("2026-11-09T10:16:00Z"):
    C.write(p2, dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
with clock("2026-11-10T10:16:00Z"):
    C.write(p2, dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
eq(F.stamp_of(p2), at("2026-11-10T10:16:00Z"), "the bound heartbeat is read")
_hb = open(F.heartbeat_path(p2), "rb").read() if os.path.exists(F.heartbeat_path(p2)) else b"{}"

# a writer that is not collect.write (a replay, a revert, a direct gzip.open) puts an
# OLDER version back with different bytes; the heartbeat must not vouch for it
with gzip.open(p2, "wt", encoding="utf-8") as fh:
    json.dump(dict(DOC, pulled_at="2026-11-08T10:16:00Z", written_at="2026-11-08T10:16:00Z"), fh)
eq(F.stamp_of(p2), at("2026-11-08T10:16:00Z"),
   "🔴 other bytes under the same name: the heartbeat is VOID, the file's own stamp is read")
eq(F.with_heartbeat(p2, raw(p2))["pulled_at"], "2026-11-08T10:16:00Z",
   "   ...by every reader of the document too")

with clock("2026-11-09T10:16:00Z"):
    C.write(p2, dict(DOC, pulled_at=C.stamp()), compress=True)
_good = sha(p2)


def planted(**over):
    b = dict(json.loads(_hb.decode("utf-8")), sha256=_good, **over)
    with open(F.heartbeat_path(p2), "w", encoding="utf-8") as fh:
        json.dump(b, fh)
    return F.stamp_of(p2)


eq(planted(), at("2026-11-10T10:16:00Z"), "   (control: a heartbeat bound to these bytes is read)")
eq(planted(file="other.json.gz"), at("2026-11-09T10:16:00Z"), "   one naming another file is void")
eq(planted(stamps={"pulled_at": "2026-11-10T10:16:00Z", "built_at": "2026-11-10T10:16:00Z",
                   "written_at": "2026-11-10T10:16:00Z"}),
   at("2026-11-09T10:16:00Z"), "   one carrying a stamp field the file does not is void")
eq(planted(stamps={"pulled_at": "yesterday", "written_at": "2026-11-10T10:16:00Z"}),
   at("2026-11-09T10:16:00Z"), "   one with an unreadable stamp is void")
os.remove(p2)
eq(F.stamp_of(p2), None, "🔴 a heartbeat beside a MISSING file vouches for nothing (MISSING)")

# ══════════════════════════════════════════════════════════════════════
section("3. THE CONTRACT: FRESH ON A STAMP-ONLY DAY, STALE ON AN OUTAGE — SAME DEADLINE")
# ══════════════════════════════════════════════════════════════════════
# A planted MLB tree, the real contract, pinned clocks. 10:00Z is the
# pitchers row's GRADING deadline (6:00 ET).
T = os.path.join(TMP, "tree").replace(os.sep, "/")
LT = T + "/data/latest"
os.makedirs(LT)
os.makedirs(T + "/picks")
PITCH = LT + "/pitchers.json.gz"


def fake(fail=False):
    """A two-arm statsapi; `fail` = the pool endpoint is down."""
    def get(url, timeout=30):
        if fail:
            raise OSError("statsapi down")
        if "stats?stats=season" in url:
            ids = (1, 2) if "playerPool=All" in url else (1,)
            return {"stats": [{"splits": [
                {"player": {"id": i, "fullName": "Arm %d" % i}, "team": {"name": "Team %d" % i},
                 "stat": {"inningsPitched": "90.0" if i == 1 else "15.0", "gamesStarted": 5,
                          "era": "3.00", "whip": "1.1", "wins": 1, "losses": 1}}
                for i in ids]}]}, {}
        if "/people?personIds=" in url:
            ids = [int(x) for x in url.split("personIds=")[1].split("&")[0].split(",")]
            return {"people": [{"id": i, "pitchHand": {"code": "R"}} for i in ids]}, {}
        return {"stats": [{"splits": [
            {"date": "2026-09-%02d" % (20 + j), "isHome": True, "opponent": {"name": "Opp %d" % j},
             "stat": {"gamesStarted": 1, "inningsPitched": "6.0", "strikeOuts": 5, "earnedRuns": 2,
                      "hits": 4, "baseOnBalls": 1, "numberOfPitches": 90, "battersFaced": 24}}
            for j in range(5)]}]}, {}
    return get


def row(now):
    rows = [r for r in F.survey(data=T + "/data", picks=T + "/picks", now=at(now))
            if r.get("path", "").endswith("/pitchers.json.gz")]
    return rows[0] if rows else None


def hard(now):
    """Is THE PULL's row hard-stale? (The mode's two table rows are built by
    run_mode after the pull, so they are not this file's question.)"""
    stale = [r for r in F.survey(data=T + "/data", picks=T + "/picks", now=at(now))
             if r.get("stale") and r["path"].endswith("/pitchers.json.gz")]
    h, _s = F.classify(stale, data=T + "/data", now=at(now))
    return {r["mode"] for r in h}


with clock("2026-11-09T10:16:00Z", LT, fake()):
    C.collect_pitchers()
_r = row("2026-11-10T09:59:00Z")
ck(_r is not None and not _r["stale"], "(control) yesterday's 10:16Z pull is fresh until 10:00Z")
_r = row("2026-11-10T10:30:00Z")
ck(_r is not None and _r["stale"] and "pitchers" in hard("2026-11-10T10:30:00Z"),
   "(control) with no pull today the row is STALE and HARD at 10:30Z (the run goes red)")

with clock("2026-11-10T10:16:00Z", LT, fake()):
    C.collect_pitchers()
ck(os.path.exists(F.heartbeat_path(PITCH)), "today's pull was stamp-only: a heartbeat, no rewrite")
_r = row("2026-11-10T10:30:00Z")
ck(_r is not None and not _r["stale"] and "pitchers" not in hard("2026-11-10T10:30:00Z"),
   "🔴🔴 a stamp-only pull keeps the row FRESH at 10:30Z: no red run, no re-plan every pass")
eq(F.age_minutes(PITCH, at("2026-11-10T10:30:00Z")), 14.0, "   its age is the pull's, to the minute")

_hb_before = open(F.heartbeat_path(PITCH), "rb").read() if os.path.exists(F.heartbeat_path(PITCH)) else None
try:
    with clock("2026-11-11T10:16:00Z", LT, fake(fail=True)):
        C.collect_pitchers()
    _died = False
except Exception:
    _died = True
ck(_died, "an outage: the pull raises, as it always has")
eq(open(F.heartbeat_path(PITCH), "rb").read() if os.path.exists(F.heartbeat_path(PITCH)) else None,
   _hb_before, "   ...and the heartbeat is NOT moved")
_r = row("2026-11-11T10:30:00Z")
ck(_r is not None and _r["stale"] and "pitchers" in hard("2026-11-11T10:30:00Z"),
   "🔴🔴 ...so the row is STALE and HARD at the same 10:00Z deadline as before "
   "(an outage is seen as fast as today)")

# ══════════════════════════════════════════════════════════════════════
section("4. THE CLASS: WHO CARRIES A HEARTBEAT, AND WHO READS ITS STAMPS")
# ══════════════════════════════════════════════════════════════════════
# 4a. The heartbeat files are DERIVED from collect.py's own call sites.
_SRC = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_TREE = ast.parse(_SRC)


def _tail(node, fn):
    """The file name a `write` call's first argument ends in (resolving a
    local `path = f"..."` in the same function)."""
    if isinstance(node, ast.Name):
        for n in ast.walk(fn):
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == node.id
                                                 for t in n.targets):
                node = n.value
                break
    parts = [v.value for v in ast.walk(node) if isinstance(v, ast.Constant) and isinstance(v.value, str)]
    return parts[-1].rsplit("/", 1)[-1] if parts else None


GZ_WRITES = {}          # function -> [(file, heartbeat?)]
for fn in ast.walk(_TREE):
    if not isinstance(fn, ast.FunctionDef):
        continue
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "write":
            kw = {k.arg: k.value for k in n.keywords}
            if isinstance(kw.get("compress"), ast.Constant) and kw["compress"].value is True:
                hb = isinstance(kw.get("heartbeat"), ast.Constant) and kw["heartbeat"].value is True
                GZ_WRITES.setdefault(fn.name, []).append((_tail(n.args[0], fn), hb))
HEARTBEAT = sorted({f for v in GZ_WRITES.values() for f, hb in v if hb})
eq(HEARTBEAT, ["hitters.json.gz", "lineups.json.gz", "pitchers.json.gz", "record-detail.json.gz",
               "scores.json.gz", "weather.json.gz"],
   "🔴 the MLB latest/ gzips measured stamp-only in winter carry a heartbeat "
   "(a change to this list is a decision: say why)")

# 4b. EVERY gzip write in collect.py decides. A new one is red until it is
#     given heartbeat=True or a reason here. (function: (gzip writes, heartbeat writes, why))
DECIDED = {
    "collect_gamelines": (1, 0, "a dated paid snapshot: written once, never in place"),
    "collect_props": (1, 0, "a dated paid snapshot"),
    "collect_alt_lines": (1, 0, "a dated paid snapshot"),
    "collect_schedule": (1, 0, "a dated schedule reading"),
    "collect_results": (1, 0, "a dated results file"),
    "collect_props_board": (1, 0, "the page fetches this file (index.html's props board): adopt only "
                                  "after a §4e decision"),
    "collect_props_board_fb": (1, 0, "football: a test patches write(path, obj, compress=False)"),
    "collect_pitchers": (1, 1, "heartbeat"),
    "collect_hitters": (1, 1, "heartbeat"),
    "collect_record": (1, 1, "heartbeat (record-detail; record.json is plain)"),
    "collect_weather": (4, 1, "the final write; the others are progress kept before a raise"),
    "collect_scores": (2, 1, "the final write; the checkpoint follows a new date"),
    "collect_lineups": (2, 1, "the final write; the checkpoint follows a new date"),
    "run_mode": (9, 0, "football's nfl-logs / fb-scores files: adopt one by one, with "
                       "their readers (§4c) and nfl.py:900-906's heartbeat rule"),
}
_got = {k: (len(v), sum(1 for _f, hb in v if hb)) for k, v in GZ_WRITES.items()}
eq(_got, {k: v[:2] for k, v in DECIDED.items()},
   "🔴 every gzip write in collect.py is decided: heartbeat, or a reason it needs none")
_direct = sorted({fn.name for fn in ast.walk(_TREE) if isinstance(fn, ast.FunctionDef)
                  for n in ast.walk(fn) if isinstance(n, ast.Call)
                  and getattr(n.func, "attr", None) == "open" and getattr(n.func.value, "id", None) == "gzip"
                  and len(n.args) > 1 and isinstance(n.args[1], ast.Constant)
                  and str(n.args[1].value).startswith("w")})
eq(_direct, ["write"], "   ...and collect.py writes a gzip directly only inside write() itself")

# 4c. EVERY scope (module body or function) in every .py here that NAMES a
#     heartbeat file and READS a stamp field must read through freshness
#     (with_heartbeat / stamp_of / age_minutes, or a same-module function
#     that calls with_heartbeat). Docstrings do not count as naming.
FIELDS = set(F.STAMP_FIELDS)
OVERLAY = {"with_heartbeat", "stamp_of", "age_minutes"}
ALLOWED = {   # (module, scope): why its stamp read is not a heartbeat file's own stamp
    ("collect.py", "collect_record"): "reads the built_at of the record doc it is writing",
    ("record_fb.py", "main"): "football's record-detail (no heartbeat): its own doc's built_at",
    ("test_record_scope.py", "run_verifier"): "plants a record-detail from its own record doc",
    ("test_card_single_day.py", "<module>"): "reads the PINNED pull it copied over the tree's "
                                             "file (any copied heartbeat is void on those bytes)",
    ("research/mlb_calibration_audit.py", "main"): "its stamp reads are the published cards' "
                                                   "(generated_at, logs_pulled_at); of the pulls it "
                                                   "reads only `season`",
}


def _scope(fn):
    out, stack = [], list(ast.iter_child_nodes(fn))
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        out.append(n)
        stack.extend(ast.iter_child_nodes(n))
    return out


def census(root, names):
    flagged, seen = [], 0
    for f in sorted(glob.glob(os.path.join(root, "*.py")) + glob.glob(os.path.join(root, "research", "*.py"))):
        src = open(f, encoding="utf-8").read()
        if not any(n in src for n in names):
            continue
        with warnings.catch_warnings():          # another module's escapes are not this test's
            warnings.simplefilter("ignore")
            tree = ast.parse(src)
        docs = {id(b.body[0].value) for b in ast.walk(tree)
                if isinstance(b, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and b.body and isinstance(b.body[0], ast.Expr)
                and isinstance(b.body[0].value, ast.Constant)}
        fns = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        ov = set(OVERLAY) | {fn.name for fn in fns
                             if any(isinstance(n, ast.Call) and getattr(n.func, "attr",
                                    getattr(n.func, "id", None)) == "with_heartbeat"
                                    for n in _scope(fn))}
        for sc in [tree] + fns:
            nodes = _scope(sc)
            if not any(isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs
                       and any(m in n.value for m in names) for n in nodes):
                continue
            reads = [n.lineno for n in nodes
                     if (isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Load)
                         and isinstance(n.slice, ast.Constant) and n.slice.value in FIELDS)
                     or (isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "get"
                         and n.args and isinstance(n.args[0], ast.Constant)
                         and n.args[0].value in FIELDS)]
            if not reads:
                continue
            seen += 1
            calls = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                     for n in nodes if isinstance(n, ast.Call)}
            key = (os.path.relpath(f, root).replace(os.sep, "/"), getattr(sc, "name", "<module>"))
            if not calls & ov and key not in ALLOWED:
                flagged.append("%s:%s line %s" % (key[0], key[1], reads[0]))
    return flagged, seen


_flag, _seen = census(ROOT, HEARTBEAT)
ck(_seen >= 8, "the census found the readers it must judge (%d scopes)" % _seen)
eq(_flag, [], "🔴🔴 no scope reads a heartbeat file's own stamp around freshness.with_heartbeat")

# rule 67: the census bites on a planted reader
_pl = os.path.join(TMP, "census")
os.makedirs(_pl)
with open(os.path.join(_pl, "reader.py"), "w", encoding="utf-8") as fh:
    fh.write("import json, gzip\n\ndef when():\n"
             "    D = json.load(gzip.open('data/latest/hitters.json.gz', 'rt'))\n"
             "    return D['pulled_at']\n")
with open(os.path.join(_pl, "fine.py"), "w", encoding="utf-8") as fh:
    fh.write("import json, gzip, freshness\n\ndef when():\n    p = 'data/latest/hitters.json.gz'\n"
             "    D = freshness.with_heartbeat(p, json.load(gzip.open(p, 'rt')))\n"
             "    return D['pulled_at']\n")
os.makedirs(os.path.join(_pl, "research"))
with open(os.path.join(_pl, "research", "audit.py"), "w", encoding="utf-8") as fh:
    fh.write("import json, gzip\n\ndef lag():\n"
             "    return json.load(gzip.open('data/latest/pitchers.json.gz', 'rt'))['pulled_at']\n")
eq(census(_pl, HEARTBEAT)[0], ["reader.py:when line 5", "research/audit.py:lag line 4"],
   "   (planted) a raw read is flagged, in research/ too; the same read through with_heartbeat is not")

# 4d. A TEST TREE COPIED FROM latest/ STARTS WITH ITS HEARTBEATS SETTLED.
#     Measured on a planted post-merge tree (live heartbeats beside the six
#     files): test_mlb_tables' LIVE extra rewrote the copied pitchers.json.gz
#     (the salted pull), voided its heartbeat, and its card's logs_pulled_at
#     no longer matched the base drive's: red on correct code.
from tcheck import copy_latest  # noqa: E402
_src = os.path.join(TMP, "settle-src")
os.makedirs(_src)
_sp = os.path.join(_src, "pitchers.json.gz")
with clock("2026-11-09T10:16:00Z"):
    C.write(_sp, dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
with clock("2026-11-10T10:16:00Z"):
    C.write(_sp, dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
_dst = os.path.join(TMP, "settle-dst")
eq(copy_latest(_src, _dst), ["pitchers.json.gz"], "copy_latest settles the heartbeat file it copies")
_cp = os.path.join(_dst, "pitchers.json.gz")
ck(not glob.glob(os.path.join(_dst, "*" + F.HEARTBEAT_SUFFIX)), "   ...and copies no heartbeat")
eq(raw(_cp)["pulled_at"], "2026-11-10T10:16:00Z", "   ...so the copy carries its OWN current stamps")
eq(raw(_cp), F.with_heartbeat(_sp, raw(_sp)), "   ...the document the source's readers see")
_nest = os.path.join(TMP, "settle-nest", "nfl", "latest")
os.makedirs(_nest)
shutil.copy(_sp, _nest)
shutil.copy(F.heartbeat_path(_sp), _nest)
eq(copy_latest(os.path.join(TMP, "settle-nest"), os.path.join(TMP, "settle-nest-dst")), ["pitchers.json.gz"],
   "   ...in a folder below the one copied too (a league's data/<lg>/latest)")

_bare_copies = []
for _t in sorted(glob.glob(os.path.join(ROOT, "test_*.py"))):
    for _n in ast.walk(ast.parse(open(_t, encoding="utf-8").read())):
        if isinstance(_n, ast.Call) and getattr(_n.func, "attr", getattr(_n.func, "id", None)) == "copytree" \
                and any(isinstance(c, ast.Constant) and isinstance(c.value, str)
                        and c.value.rstrip("/").split("/")[-1] == "latest"
                        for a in _n.args[:1] for c in ast.walk(a)):
            _bare_copies.append("%s:%d" % (os.path.basename(_t), _n.lineno))
eq(_bare_copies, [], "🔴 no test copies a latest/ directory around tcheck.copy_latest")


def single_copies(paths):
    """`shutil.copy*` / `copyfile` of a heartbeat file OUT of a latest/ path: its heartbeat would be left behind."""
    out = []
    for _t in paths:
        for _n in ast.walk(ast.parse(open(_t, encoding="utf-8").read())):
            if isinstance(_n, ast.Call) and getattr(_n.func, "attr", None) in ("copy", "copy2", "copyfile") \
                    and _n.args:
                parts = [c.value for c in ast.walk(_n.args[0]) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
                if "latest" in parts and any(p in HEARTBEAT for p in parts):
                    out.append("%s:%d" % (os.path.basename(_t), _n.lineno))
    return out


eq(single_copies(sorted(glob.glob(os.path.join(ROOT, "test_*.py")))), [],
   "🔴 no test copies one heartbeat file out of latest/ without its heartbeat")
with open(os.path.join(_pl, "test_bad.py"), "w", encoding="utf-8") as fh:
    fh.write("import os, shutil\nshutil.copy(os.path.join('data', 'latest', 'hitters.json.gz'), 'x')\n")
eq(single_copies([os.path.join(_pl, "test_bad.py")]), ["test_bad.py:2"], "   (planted) one is flagged")

# ══════════════════════════════════════════════════════════════════════
section("4e. THE PAGE NEVER READS A HEARTBEAT FILE'S STAMP")
# ══════════════════════════════════════════════════════════════════════
# The page fetches record-detail (the Track Record's days) and reads only its rows. A
# page that printed a heartbeat file's own stamp would show the last CHANGE, not the
# last pull; it must read the time from a plain file (freshness.json) instead.
import re  # noqa: E402


def page_reads(text):
    """-> (the variables the page fills from a heartbeat file, those it reads a stamp off,
    whether it ever fetches a .beat.json)."""
    code = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    code = "\n".join(re.sub(r"(^|\s)//.*$", "", ln) for ln in code.split("\n"))
    held = {m.group(1) for m in re.finditer(
        r"\b([A-Za-z_$][\w$]*)\s*=\s*await\s+jget(?:Gz)?\(\s*['\"`]([^'\"`]+)['\"`]", code)
        if m.group(2).rsplit("/", 1)[-1] in HEARTBEAT}
    stamped = {m.group(1) for m in re.finditer(
        r"\b([A-Za-z_$][\w$]*)\s*(?:\.(?:%s)\b|\[\s*['\"](?:%s)['\"]\s*\])"
        % ("|".join(F.STAMP_FIELDS), "|".join(F.STAMP_FIELDS)), code)}
    return held, held & stamped, ".beat.json" in code
_page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
_held, _bad_reads, _beat = page_reads(_page)
ck("RECDETAIL" in _held, "(the census sees the page's record-detail fetch)", sorted(_held))
eq((sorted(_bad_reads), _beat), ([], False),
   "🔴 the page reads no stamp of a heartbeat file, and never fetches a .beat.json")
eq(sorted(page_reads(_page + "\nconst x = `${RECDETAIL.built_at}`;\n")[1]), ["RECDETAIL"],
   "   (planted) a page read of record-detail's built_at is flagged")

# ══════════════════════════════════════════════════════════════════════
section("5. THE REAL CHAIN: TWO IDENTICAL PITCHER PULLS, THEN THE TABLES")
# ══════════════════════════════════════════════════════════════════════
L5 = os.path.join(TMP, "chain", "latest")
L6 = os.path.join(TMP, "chain-old", "latest")
os.makedirs(L5)
os.makedirs(L6)
with clock("2026-11-09T10:16:00Z", L5, fake()):
    C.collect_pitchers()
with clock("2026-11-09T10:16:00Z", L6, fake()):
    C.collect_pitchers()
_p5 = sha(os.path.join(L5, "pitchers.json.gz"))
with clock("2026-11-10T10:16:00Z", L5, fake()):
    C.collect_pitchers()
eq(sha(os.path.join(L5, "pitchers.json.gz")), _p5, "🔴 the second identical pull is not stored again")
# the world as it was: the same pull written in full
with clock("2026-11-10T10:16:00Z", L6, fake()):
    C.write(os.path.join(L6, "pitchers.json.gz"),
            dict({k: v for k, v in raw(os.path.join(L6, "pitchers.json.gz")).items()
                  if k != "written_at"}, pulled_at=C.stamp()), compress=True)
_new, _old = (M.build(os.path.join(d, "pitchers.json.gz"), built_at="X")
              for d in (L5, L6))
eq(_new, _old, "🔴🔴 the pitcher and opponent tables are byte-for-byte the full write's "
               "(through, source_pulled_at)")
eq(_new[0]["source_pulled_at"], "2026-11-10T10:16:00Z", "   source_pulled_at is today's pull")

# 5b. THE REAL SHAPE: a real pull (the frozen 2026-10-17 one) written again with tomorrow's
#     stamps is recognised as unchanged and aged by tomorrow (int ids, nesting, every field).
_real = os.path.join(ROOT, "research", "mlb_pitchers_20261017.json.gz")
_R5 = os.path.join(TMP, "real")
os.makedirs(_R5)
_rp = os.path.join(_R5, "pitchers.json.gz")
shutil.copy(_real, _rp)
_doc = {k: v for k, v in raw(_rp).items() if k not in F.STAMP_FIELDS}
_doc["players"] = {int(k): v for k, v in _doc["players"].items()}       # as the pull builds it
_before5 = sha(_rp)
with clock("2026-10-18T10:16:00Z"):
    C.write(_rp, dict(_doc, pulled_at=C.stamp()), compress=True, heartbeat=True)
eq((sha(_rp), F.stamp_of(_rp)), (_before5, at("2026-10-18T10:16:00Z")),
   "🔴 a real pull's next identical pull keeps its bytes and is aged by the new pull")
for _f in HEARTBEAT:
    _lp = os.path.join(ROOT, "data", "latest", _f)
    note("live %s: %s" % (_f, "heartbeat beside it" if os.path.exists(F.heartbeat_path(_lp)) else "no heartbeat"))
shutil.rmtree(TMP, ignore_errors=True)
