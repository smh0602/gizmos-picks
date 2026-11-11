#!/usr/bin/env python3
"""🔴 A STAMP-ONLY REWRITE OF A GZIP IS A HEARTBEAT, NOT A COPY — AND THE
HEARTBEAT IS MOVED, NEVER DROPPED. `[2026-10-28]`

The defect: `collect.write` rewrote a gzip whose content had not changed,
because its stamps moved. Git deltas a gzip only when its compressed bytes
happen to survive the change, so such a rewrite was often a whole copy kept
for ever: pitchers.json.gz + hitters.json.gz were the same content from
2026-10-01 to 10-27 and wrote ~590 KB a day of raw gzip.

The trap beside it (nfl.py, 2026-10-26): the rewrite IS the outage alarm.
A skip that drops the stamp leaves the row stale on a healthy day (a red
run), and the first fix of that kind hid a 10-day nflverse outage. So:

  §1  write(heartbeat=True) keeps the gzip's bytes and writes the heartbeat;
      the document every reader sees is EXACTLY the full write's.
  §2  the heartbeat is bound to the file's exact bytes: anything else that
      touches the file voids it (stale, never falsely fresh); it is one line,
      so git's merge of two runs' heartbeats keeps one whole (test_push_retry
      §5: a landing never puts one beside bytes it does not vouch for).
  §3  the contract: a stamp-only pull keeps the row fresh, a failed pull
      leaves it stale at the same deadline as before.
  §4  the CLASS: every scope that names a heartbeat file and reads a stamp
      reads it through freshness; every gzip write decides, ~~in collect.py
      only~~ `[2026-11-10]` in every module (§4b, §4b'); only collect.write
      makes a heartbeat (called from any module: §4a lists each, by module and
      file); no test copies one out of latest/ unsettled, a league's included;
      the page reads no heartbeat file's stamp.
  §3b `[2026-11-10]` football: the card-fb rows (dossiers, game lines) on a
      planted league tree, the same two answers as §3.
  §5  the real chain: two identical pitcher pulls, then the tables.

⛔ A TEST ASKS THE CODE: every tree here is planted, every clock pinned.

# @vacuity 🔴 a skip that DROPS the heartbeat (nfl.py's 10-day lesson) is caught
#   file: freshness.py
#   find:         os.replace(tmp, hp)
#   with:         pass
#
# @vacuity 🔴 a heartbeat that is not bound to the file's bytes is caught
#   file: freshness.py
#   find:     if beat.get("sha256") != hashlib.sha256(buf).hexdigest():
#   with:     if False:
#
# @vacuity 🔴 [2026-10-28] a heartbeat is ONE line, so git's merge of two keeps one side whole
#   file: freshness.py
#   find:             fh.write(json.dumps(beat, separators=(",", ":"))
#   with:             fh.write(json.dumps(beat, indent=1)
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
# @vacuity 🔴 [2026-10-28] a raw read beside an overlay of ANOTHER heartbeat file is caught (card.main)
#   file: card.py
#   find:     P = load(f"{LATEST}/pitchers.json.gz", gz=True)
#   with:     P = json.load(gzip.open(f"{LATEST}/pitchers.json.gz", "rt"))
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
# @vacuity 🔴 [2026-11-10] the football dossiers that stopped passing heartbeat=True are caught
#   file: dossier_fb.py
#   find:     _C.write(p, doc, compress=True, heartbeat=True)
#   with:     _C.write(p, doc, compress=True)
#
# @vacuity 🔴 [2026-11-10] ...and the game lines
#   file: game_lines_fb.py
#   find:     collect.write(path, doc, compress=True, heartbeat=True)
#   with:     collect.write(path, doc, compress=True)
#
# @vacuity 🔴 [2026-11-10] ...and the football record-detail
#   file: record_fb.py
#   find:              compress=True, heartbeat=True)
#   with:              compress=True)
#
# @vacuity 🔴 [2026-11-10] the card's raw read of the ladder's stamp is caught
#   file: card_fb.py
#   find:         _ladder = _F.with_heartbeat(_lp, json.load(gzip.open(_lp, "rt")))
#   with:         _ladder = json.load(gzip.open(_lp, "rt"))
#
# @vacuity 🔴 [2026-11-10] a gzip writer outside collect.py that has not decided is caught
#   file: fb_weather.py
#   find:         with gzip.open(path, "wt", encoding="utf-8") as fh:
#   with:         with gzip.open(path, "wt", encoding="utf-8") as fh, gzip.open(path + ".x", "wt") as _x:
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
import re
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
# (2b: it is one line, so a merge keeps one side whole)
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

# 2b. `[2026-10-28, review; measured]` TWO RUNS' HEARTBEATS MERGED BY GIT KEEP ONE SIDE
#     WHOLE. push_retry.sh rebases with `-X theirs`. Indented, git took the lines only
#     the tip changed (sha256) from the tip and the conflicting ones (stamps) from this
#     run: a SPLICE that bound, vouching this run's time for bytes it never compared.
#     One line conflicts whole, so the merge keeps one run's heartbeat as it wrote it.
import subprocess  # noqa: E402
M2 = os.path.join(TMP, "merge")
_mp = {t: os.path.join(M2, t, "logs.json.gz") for t in ("base", "tip", "mine")}
for _t in _mp:
    os.makedirs(os.path.dirname(_mp[_t]))
with clock("2026-11-09T08:00:00Z"):
    C.write(_mp["base"], dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
with clock("2026-11-09T10:16:00Z"):
    C.write(_mp["base"], dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
shutil.copy(_mp["base"], _mp["mine"])                       # this run: the base's bytes...
with clock("2026-11-11T10:16:00Z"):                         # ...seen unchanged later
    C.write(_mp["mine"], dict(DOC, pulled_at=C.stamp()), compress=True, heartbeat=True)
with clock("2026-11-10T08:00:00Z"):                         # the tip: new content...
    C.write(_mp["tip"], dict(DOC, season=2027, pulled_at=C.stamp()), compress=True, heartbeat=True)
with clock("2026-11-10T10:16:00Z"):                         # ...then seen unchanged
    C.write(_mp["tip"], dict(DOC, season=2027, pulled_at=C.stamp()), compress=True, heartbeat=True)
_hp = {t: F.heartbeat_path(p) for t, p in _mp.items()}
ck(all(os.path.exists(p) for p in _hp.values()) and sha(_mp["base"]) == sha(_mp["mine"]) != sha(_mp["tip"]),
   "(planted: three heartbeats, the base's and this run's on the same bytes, the tip's on new ones)")
ck(all(open(p, encoding="utf-8").read().count("\n") == 1 for p in _hp.values()),
   "   a heartbeat is ONE line of JSON")
_mg = subprocess.run(["git", "merge-file", "-p", "--theirs", _hp["tip"], _hp["base"], _hp["mine"]],
                     capture_output=True)
with open(_hp["tip"], "wb") as fh:                          # the rebase's result, beside the tip's gzip
    fh.write(_mg.stdout)
eq(F.stamp_of(_mp["tip"]) in (at("2026-11-10T10:16:00Z"), at("2026-11-10T08:00:00Z")), True,
   "🔴 git's merge of two runs' heartbeats never vouches one run's time for the other's bytes "
   "(%s)" % F.stamp_of(_mp["tip"]))

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

# 3b. `[2026-11-10]` FOOTBALL: card-fb's dossiers and game lines on a planted league tree, the
#     real contract. A pass whose files moved only their stamps keeps both rows fresh at the
#     card deadline; a day with no card-fb pass leaves them stale and hard, as before.
FT = os.path.join(TMP, "fbtree").replace(os.sep, "/")
FL = FT + "/data/nfl/latest"
os.makedirs(FL)
os.makedirs(FT + "/picks")
open(FL + "/props.json.gz", "wb").close()        # a board was pulled: the card's rows exist
FB = {"dossiers.json.gz": {"league": "nfl", "dossiers": [{"board_id": 7, "sections": []}]},
      "game-lines.json.gz": {"league": "nfl", "games": [], "n_rungs": 0}}


def fbrows(now):
    return {r["path"].rsplit("/", 1)[-1]: r for r in F.survey(data=FT + "/data/nfl", picks=FT + "/picks", now=at(now))
            if r["path"].rsplit("/", 1)[-1] in FB}


def fbwrite(when):
    with clock(when):
        for name, doc in FB.items():
            C.write(FL + "/" + name, dict(doc, built_at=C.stamp()), compress=True, heartbeat=True)


fbwrite("2026-11-08T12:00:00Z")
_due = {k: r["due_at"] for k, r in fbrows("2026-11-10T20:00:00Z").items()}
eq(sorted(_due), sorted(FB), "the card-fb rows judge both files (%s)" % _due)
_d = max(_due.values())                           # the latest card deadline before 20:00Z, as both read it
_t1 = (at(_d[:-1] + ":00Z") + datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
_t2 = (at(_d[:-1] + ":00Z") + datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
_shas = {k: sha(FL + "/" + k) for k in FB}
fbwrite(_t1)
eq({k: sha(FL + "/" + k) for k in FB}, _shas, "a stamp-only card-fb pass leaves both gzips' bytes as they were")
ck(all(os.path.exists(F.heartbeat_path(FL + "/" + k)) for k in FB), "   ...and writes both heartbeats")
_r = fbrows(_t2)
ck(len(_r) == 2 and not any(r["stale"] for r in _r.values()),
   "🔴🔴 ...so both rows are FRESH after the card deadline (%s): no red run, no re-plan every pass" % _d, _r)
_r = fbrows((at(_t2) + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))
_hard, _soft = F.classify([r for r in _r.values() if r["stale"]], data=FT + "/data/nfl",
                          now=at(_t2) + datetime.timedelta(days=1))
ck(len(_r) == 2 and all(r["stale"] for r in _r.values()) and {r["mode"] for r in _hard} == {"card-fb"},
   "🔴🔴 a day with no card-fb pass: both rows STALE and HARD at the same deadline (an outage is seen "
   "as fast as today)", (_r, _hard))

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


def collect_aliases(tree):
    """`[2026-11-10]` The names a module binds to collect (`import collect [as X]`, anywhere)."""
    return {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.Import)
            for a in n.names if a.name == "collect"}


def is_collect_write(n, rel, aliases):
    """Is call `n` collect.write? collect.py's own `write(...)`, or `<alias>.write(...)`."""
    f = n.func
    return ((rel == "collect.py" and isinstance(f, ast.Name) and f.id == "write")
            or (isinstance(f, ast.Attribute) and f.attr == "write"
                and isinstance(f.value, ast.Name) and f.value.id in aliases))


def _parse_mod(path):
    with warnings.catch_warnings():               # another module's escapes are not this test's
        warnings.simplefilter("ignore")
        return ast.parse(open(path, encoding="utf-8").read())


def gz_writes(path, rel):
    """{function: [(file, heartbeat?)]} of every collect.write(..., compress=True) in the
    module at `path` (`rel`: its name here)."""
    tree = _parse_mod(path)
    al, out = collect_aliases(tree), {}
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef):
            continue
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and is_collect_write(n, rel, al):
                kw = {k.arg: k.value for k in n.keywords}
                if isinstance(kw.get("compress"), ast.Constant) and kw["compress"].value is True:
                    hb = isinstance(kw.get("heartbeat"), ast.Constant) and kw["heartbeat"].value is True
                    out.setdefault(fn.name, []).append((_tail(n.args[0], fn), hb))
    return out


def modules(root):
    """[(path, name here)] of every module in `root` and research/, tests left out."""
    return [(f, os.path.relpath(f, root).replace(os.sep, "/"))
            for f in sorted(glob.glob(os.path.join(root, "*.py")) + glob.glob(os.path.join(root, "research", "*.py")))
            if not os.path.basename(f).startswith("test_")]


GZ_WRITES = gz_writes(os.path.join(ROOT, "collect.py"), "collect.py")     # collect.py's (§4b)
HB_WRITES = sorted({(rel, f) for p, rel in modules(ROOT) for v in gz_writes(p, rel).values()
                    for f, hb in v if hb})
eq(HB_WRITES, [("collect.py", "hitters.json.gz"), ("collect.py", "lineups.json.gz"),
               ("collect.py", "pitchers.json.gz"), ("collect.py", "record-detail.json.gz"),
               ("collect.py", "scores.json.gz"), ("collect.py", "weather.json.gz"),
               ("dossier_fb.py", "dossiers.json.gz"), ("game_lines_fb.py", "game-lines.json.gz"),
               ("record_fb.py", "record-detail.json.gz")],
   "🔴 the MLB latest/ gzips measured stamp-only in winter, and `[2026-11-10]` football's dossiers, "
   "game lines and record-detail (291 of 439 rewrites 11-03 -> 11-10, 19.0 MB, stamp-only), carry a "
   "heartbeat, by module and file (a change to this list is a decision: say why)")
HEARTBEAT = sorted({f for _m, f in HB_WRITES})
_pa = os.path.join(TMP, "aliases")
os.makedirs(_pa)
with open(os.path.join(_pa, "other.py"), "w", encoding="utf-8") as fh:
    fh.write("def put(p, d):\n    import collect as K\n"
             "    K.write(p + '/x.json.gz', d, compress=True, heartbeat=True)\n")
eq(gz_writes(os.path.join(_pa, "other.py"), "other.py"), {"put": [("x.json.gz", True)]},
   "   (planted) a heartbeat write through any name a module gives collect is listed")

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

# 4b'. `[2026-11-10]` ...AND EVERY gzip WRITE IN EVERY OTHER MODULE DECIDES: a gzip opened
#      for writing (`gzip.open` or `GzipFile` with a w/a/x mode, or a mode it cannot read)
#      or a collect.write(compress=True). A new one is red until it is given heartbeat=True
#      or a reason. ("module:function": (gzip writes, heartbeat writes, why))
REPO_DECIDED = {
    "cfb.py:write_stamped": (1, 0, "college's CFBD files (schedule, players, vs-position, ...): their "
                                   "stamps are read raw (cfb.fetch_adv's daily gate, the page's "
                                   "fbScores and renderFootball): adopt with their readers"),
    "cfb_injuries.py:_write_gz": (1, 0, "written on a change only, with mtime 0 and sorted keys: the same "
                                       "content is the same bytes"),
    "daystore.py:archive": (1, 0, "a dated, write-once archive, never in place (`same_as` copies "
                                  "latest's bytes)"),
    "dossier_fb.py:build": (1, 1, "heartbeat"),
    "fb_history.py:_write": (1, 0, "an older season, written once while missing"),
    "fb_weather.py:run": (1, 0, "stored-only forecasts whose `last` moves every run: content"),
    "game_lines_fb.py:build": (1, 1, "heartbeat"),
    "mlb_refit.py:main": (2, 0, "the refit's start logs, its own weekly job's"),
    "nfl.py:store_injuries": (1, 0, "nfl-logs' injuries: their own on-change rule on the game-day check "
                                    "(nfl.py:900-906's heartbeat rule); adopt with nfl-logs' files"),
    "offseason.py:_open": (1, 0, "the off-season job's throwaway checkout: it settles a heartbeat "
                                 "before it rewrites (blank)"),
    "record_fb.py:main": (1, 1, "heartbeat"),
    "t60r.py:grade": (1, 0, "the pre-registered T60r report, research output of a mode"),
    "t60r.py:lines": (1, 0, "T60r's CFBD closing lines, research input of a mode"),
    "tcheck.py:copy_latest": (1, 0, "a test tree's settled copy"),
}


def _mode_writes(n):
    """Does a gzip open / GzipFile call open for writing (a w/a/x mode, or one it cannot read)?
    `[review]` GzipFile's mode is its second positional argument too."""
    m = n.args[1] if len(n.args) > 1 else None
    m = next((k.value for k in n.keywords if k.arg == "mode"), m)
    if m is None:
        return False                                    # the default mode reads
    return not isinstance(m, ast.Constant) or str(m.value)[:1] in "wax"


def gzip_names(tree):
    """`[review]` (names bound to the gzip module, {name: gzip function} bound by `from gzip
    import ...`): `import gzip as _gz` is the repo's own spelling (nfl.py, cfb.py)."""
    mods, funcs = set(), {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.asname or a.name for a in n.names if a.name == "gzip"}
        elif isinstance(n, ast.ImportFrom) and n.module == "gzip":
            funcs.update({a.asname or a.name: a.name for a in n.names})
    return mods, funcs


def gz_sites(path, rel):
    """{"module:function": [heartbeat?]} of every gzip write in a module but collect.py: a gzip
    open / GzipFile for writing and gzip.compress, through any name the module gives gzip; a
    collect.write whose compress is not a literal False, through any name it gives collect or
    its `write`. Module-level statements are scope "<module>"."""
    tree = _parse_mod(path)
    al, out = collect_aliases(tree), {}
    gmods, gfuncs = gzip_names(tree)
    cw_names = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                and n.module == "collect" for a in n.names if a.name == "write"}

    def gz_call(n):
        f = n.func
        what = (f.attr if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in gmods
                else gfuncs.get(f.id) if isinstance(f, ast.Name) else None)
        return what == "compress" or (what in ("open", "GzipFile") and _mode_writes(n))

    def cw_call(n):
        if not (is_collect_write(n, rel, al) or (isinstance(n.func, ast.Name) and n.func.id in cw_names)):
            return False
        c = next((k.value for k in n.keywords if k.arg == "compress"), n.args[2] if len(n.args) > 2 else None)
        return c is not None and not (isinstance(c, ast.Constant) and c.value in (False, None, 0))
    def own(fn):                                         # the function's own nodes, not a nested def's
        nodes, stack = [], list(ast.iter_child_nodes(fn))
        while stack:
            x = stack.pop()
            if not isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nodes.append(x)
                stack.extend(ast.iter_child_nodes(x))
        return nodes
    for sc in [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for n in own(sc):
            if not isinstance(n, ast.Call):
                continue
            kw = {k.arg: k.value for k in n.keywords}
            cw = cw_call(n)
            if gz_call(n) or cw:
                out.setdefault("%s:%s" % (rel, getattr(sc, "name", "<module>")), []).append(
                    bool(cw and isinstance(kw.get("heartbeat"), ast.Constant) and kw["heartbeat"].value is True))
    return out


_sites = {k: v for p, rel in modules(ROOT) if rel != "collect.py" for k, v in gz_sites(p, rel).items()}
eq({k: (len(v), sum(v)) for k, v in sorted(_sites.items())},
   {k: v[:2] for k, v in sorted(REPO_DECIDED.items())},
   "🔴🔴 every gzip write outside collect.py is decided too: heartbeat, or a reason it needs none")
with open(os.path.join(_pa, "writer.py"), "w", encoding="utf-8") as fh:
    fh.write("import gzip, json\n\ndef a(p):\n    with gzip.open(p, 'wt') as fh:\n        json.dump({}, fh)\n\n"
             "def b(p, m):\n    return gzip.open(p, m)\n\ndef c(p):\n    return gzip.GzipFile(p, mode='wb')\n\n"
             "def d(p):\n    return json.load(gzip.open(p, 'rt'))\n\ndef e(p):\n    return gzip.open(p)\n")
with open(os.path.join(_pa, "spell.py"), "w", encoding="utf-8") as fh:   # `[review]` every other spelling
    fh.write("import gzip as _gz\nfrom gzip import GzipFile as GF, open as gopen\nimport collect as K\n"
             "from collect import write as W\n_gz.open('m.json.gz', 'wt')\n\n"
             "def f(p):\n    return _gz.open(p, 'wt')\n\ndef g(p):\n    return _gz.GzipFile(p, 'wb')\n\n"
             "def h(p):\n    return GF(p, 'wb')\n\ndef i(p):\n    return gopen(p, 'at')\n\n"
             "def j(b):\n    return _gz.compress(b)\n\ndef k(p, d):\n    W(p, d, compress=True)\n\n"
             "def l(p, d, z):\n    K.write(p, d, z)\n\ndef m(p):\n    return _gz.open(p, 'rt')\n\n"
             "def n(p, d):\n    K.write(p, d, compress=False)\n")
eq(sorted(gz_sites(os.path.join(_pa, "writer.py"), "writer.py")), ["writer.py:a", "writer.py:b", "writer.py:c"],
   "   (planted) a w mode, a mode it cannot read and a GzipFile are writes; a read is not")
eq(sorted(gz_sites(os.path.join(_pa, "spell.py"), "spell.py")),
   ["spell.py:<module>", "spell.py:f", "spell.py:g", "spell.py:h", "spell.py:i", "spell.py:j", "spell.py:k",
    "spell.py:l"],
   "   (planted, review) an aliased gzip, a from-import, GzipFile's positional mode, gzip.compress, a "
   "module-level write, `from collect import write` and a computed compress are writes too; a read and "
   "compress=False are not")


# 4c. EVERY scope (module body or function) in every .py here that NAMES a
#     heartbeat file and READS a stamp field must read through freshness
#     (with_heartbeat / stamp_of / age_minutes, or a same-module function
#     that calls with_heartbeat). Docstrings do not count as naming.
FIELDS = set(F.STAMP_FIELDS)
OVERLAY = {"with_heartbeat", "stamp_of", "age_minutes"}
ALLOWED = {   # (module, scope): why its stamp read is not a heartbeat file's own stamp
    ("collect.py", "collect_record"): "reads the built_at of the record doc it is writing",
    ("record_fb.py", "main"): "the built_at of the record doc it is writing (record.json), which it "
                              "also gives record-detail's write `[2026-11-10]` (~~no heartbeat~~)",
    ("test_record_scope.py", "run_verifier"): "plants a record-detail from its own record doc",
    ("test_card_single_day.py", "<module>"): "reads the PINNED pull it copied over the tree's "
                                             "file (any copied heartbeat is void on those bytes)",
    ("test_mlb_tables.py", "<module>"): "reads the PINNED pull it copied over the planted tree's file "
                                        "(copy_latest left no heartbeat beside it)",
    ("test_heartbeat.py", "<module>"): "this test reads gzips' OWN stamps on purpose, to show what the "
                                       "heartbeat changes and what it does not",
    ("test_dossier_fb.py", "<module>"): "`[2026-11-10]` reads the first pass's latest/ dossiers raw on "
                                        "purpose: its check is that the second pass's heartbeat carries a "
                                        "NEW built_at over the same bytes",
    ("test_offseason.py", "<module>"): "`[2026-11-10]` reads the emptied game lines raw on purpose: blank "
                                       "must write the heartbeat's stamps INTO the file it rewrites",
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


def _consts(node):
    return [c.value for c in ast.walk(node) if isinstance(c, ast.Constant) and isinstance(c.value, str)]


def _overlay(n, local_ov, names):
    """Is call `n` a read through freshness? `[2026-10-28, review]` ⛔ `json.load` is not
    the module's own `load()`: a same-module overlay counts only as a BARE call, and
    freshness's own only by name. And an overlay whose path is a literal naming
    ANOTHER file (`F.stamp_of('.../board.json')`) covers nothing."""
    f = n.func
    if isinstance(f, ast.Name):
        ok = f.id in local_ov or f.id in OVERLAY
    else:
        ok = isinstance(f, ast.Attribute) and f.attr in OVERLAY
    if not ok or not n.args:
        return ok
    lits = _consts(n.args[0])
    return (any(m in c for c in lits for m in names)
            or not any(re.search(r"\.json(\.gz)?$", c) for c in lits))


def _assigns(nodes):
    """{name: [values]} bound in a scope: assignments and `with ... as name`."""
    out = {}
    for n in nodes:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out.setdefault(t.id, []).append(n.value)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            out.setdefault(n.target.id, []).append(n.value)
        elif isinstance(n, (ast.With, ast.AsyncWith)):
            for it in n.items:
                if isinstance(it.optional_vars, ast.Name):
                    out.setdefault(it.optional_vars.id, []).append(it.context_expr)
    return out


def _names_hb(e, env, held, names, depth=0):
    """Does expression `e` name a heartbeat file (a literal, a module-level path,
    or a name this scope bound to one)?"""
    for n in ast.walk(e):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and any(m in n.value for m in names):
            return True
        if isinstance(n, ast.Name) and (n.id in held or (depth < 3 and any(
                _names_hb(v, env, held, names, depth + 1) for v in env.get(n.id, ()) if v is not e))):
            return True
    return False


def _judge(r, env, held, local_ov, names, depth=0):
    """What the document a stamp is read off is: "ok" (it came through an overlay),
    "raw" (a heartbeat file loaded around one) or "unknown". `[2026-10-28, review]`
    Each read is judged by ITS value: one overlay of another file in the same scope
    covered card.main's raw read of pitchers.json.gz."""
    while isinstance(r, (ast.Subscript, ast.Attribute)):
        r = r.value
    if isinstance(r, ast.Name):
        js = [_judge(v, env, held, local_ov, names, depth + 1) for v in env.get(r.id, ())
              if depth < 4] if r.id in env else []
        return "ok" if "ok" in js else "raw" if "raw" in js else "unknown"
    if any(isinstance(n, ast.Call) and _overlay(n, local_ov, names) for n in ast.walk(r)):
        return "ok"
    return "raw" if _names_hb(r, env, held, names) else "unknown"


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
        # a module-level name bound to a path that names a heartbeat file
        held = {t.id for st in tree.body if isinstance(st, ast.Assign)
                for t in st.targets if isinstance(t, ast.Name)
                and any(m in c for c in _consts(st.value) for m in names)}
        fns = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        local_ov = {fn.name for fn in fns
                    if any(isinstance(n, ast.Call) and (getattr(n.func, "attr", None)
                                                        or getattr(n.func, "id", None)) == "with_heartbeat"
                           for n in _scope(fn))}
        for sc in [tree] + fns:
            nodes = _scope(sc)
            if not any((isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs
                        and any(m in n.value for m in names))
                       or (isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in held)
                       for n in nodes):
                continue
            reads = [(n.lineno, n.value if isinstance(n, ast.Subscript) else n.func.value) for n in nodes
                     if (isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Load)
                         and isinstance(n.slice, ast.Constant) and n.slice.value in FIELDS)
                     or (isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "get"
                         and n.args and isinstance(n.args[0], ast.Constant)
                         and n.args[0].value in FIELDS)]
            if not reads:
                continue
            seen += 1
            env = _assigns(nodes)
            got = [(ln, _judge(r, env, held, local_ov, names)) for ln, r in reads]
            covered = any(isinstance(n, ast.Call) and _overlay(n, local_ov, names) for n in nodes)
            bad = [ln for ln, j in got if j == "raw"] or ([] if covered else [ln for ln, j in got if j != "ok"])
            key = (os.path.relpath(f, root).replace(os.sep, "/"), getattr(sc, "name", "<module>"))
            if bad and key not in ALLOWED:
                flagged.append("%s:%s line %s" % (key[0], key[1], bad[0]))
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
# `[2026-10-28, review]` the three shapes the first census passed: json.load beside the
#    module's own load() overlay, an overlay of ANOTHER file in the same scope, and a
#    path held in a module-level constant
with open(os.path.join(_pl, "collide.py"), "w", encoding="utf-8") as fh:
    fh.write("import json, gzip, freshness as F\n\ndef load(p):\n"
             "    return F.with_heartbeat(p, json.load(gzip.open(p, 'rt')))\n\ndef when():\n"
             "    D = json.load(gzip.open('data/latest/hitters.json.gz', 'rt'))\n"
             "    return D['pulled_at']\n")
with open(os.path.join(_pl, "mixed.py"), "w", encoding="utf-8") as fh:
    fh.write("import json, gzip, freshness as F\n\ndef when():\n"
             "    F.stamp_of('data/latest/board.json')\n"
             "    D = json.load(gzip.open('data/latest/hitters.json.gz', 'rt'))\n"
             "    return D.get('pulled_at')\n")
with open(os.path.join(_pl, "constpath.py"), "w", encoding="utf-8") as fh:
    fh.write("import json, gzip\nP = 'data/latest/pitchers.json.gz'\n\ndef lag():\n"
             "    return json.load(gzip.open(P, 'rt'))['pulled_at']\n")
with open(os.path.join(_pl, "same.py"), "w", encoding="utf-8") as fh:   # card.main's shape
    fh.write("import json, gzip, freshness as F\n\ndef load(p):\n"
             "    return F.with_heartbeat(p, json.load(gzip.open(p, 'rt')))\n\ndef main():\n"
             "    H = load('data/latest/hitters.json.gz')\n"
             "    P = json.load(gzip.open('data/latest/pitchers.json.gz', 'rt'))\n"
             "    return H.get('pulled_at'), P.get('pulled_at')\n")
with open(os.path.join(_pl, "fine2.py"), "w", encoding="utf-8") as fh:   # ...and its fixed form
    fh.write("import json, gzip, freshness as F\n\ndef load(p):\n"
             "    return F.with_heartbeat(p, json.load(gzip.open(p, 'rt')))\n\ndef main():\n"
             "    path = 'data/latest/pitchers.json.gz'\n"
             "    with gzip.open(path, 'rt') as fh:\n        P = json.load(fh)\n"
             "    P = F.with_heartbeat(path, P)\n"
             "    H = load('data/latest/hitters.json.gz')\n"
             "    return H.get('pulled_at'), P['pulled_at']\n")
eq(census(_pl, HEARTBEAT)[0], ["collide.py:when line 8", "constpath.py:lag line 5", "mixed.py:when line 6",
                               "reader.py:when line 5", "research/audit.py:lag line 4", "same.py:main line 9"],
   "   (planted) a raw read is flagged, in research/ too, beside the module's own load(), beside "
   "an overlay of another file or of ANOTHER heartbeat file (card.main's shape), and through a "
   "module-level path; the same reads through with_heartbeat are not")


# 4c'. `[2026-10-28, review]` ...AND ONLY collect.write MAKES A HEARTBEAT, so the files the
#      censuses judge are every heartbeat file there is. A module that kept a gzip through
#      keep_with_heartbeat itself, or passed `heartbeat=` to a write of its own, would
#      carry one no census here ever judged.
def keepers(root):
    out = []
    for f in sorted(glob.glob(os.path.join(root, "*.py")) + glob.glob(os.path.join(root, "research", "*.py"))):
        rel = os.path.relpath(f, root).replace(os.sep, "/")
        src = open(f, encoding="utf-8").read()
        if os.path.basename(f).startswith("test_") or ("keep_with_heartbeat" not in src and "heartbeat=" not in src):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(src)
        for sc in [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for n in _scope(sc):
                if not isinstance(n, ast.Call):
                    continue
                if (getattr(n.func, "attr", None) or getattr(n.func, "id", None)) == "keep_with_heartbeat":
                    out.append((rel, getattr(sc, "name", "<module>"), "keep_with_heartbeat"))
                # `[2026-11-10]` ~~any heartbeat= outside collect.py~~ a heartbeat= on anything but
                #    a collect.write call §4a LISTS (a literal compress=True and heartbeat=True):
                #    `[review]` a positional or computed compress makes a heartbeat no list holds
                kw = {k.arg: k.value for k in n.keywords}
                listed = (is_collect_write(n, rel, collect_aliases(tree))
                          and isinstance(kw.get("compress"), ast.Constant) and kw["compress"].value is True
                          and isinstance(kw.get("heartbeat"), ast.Constant) and kw["heartbeat"].value is True)
                if not listed and "heartbeat" in kw and not (
                        isinstance(kw["heartbeat"], ast.Constant) and kw["heartbeat"].value is False):
                    out.append((rel, getattr(sc, "name", "<module>"), "heartbeat="))
    return out


eq(keepers(ROOT), [("collect.py", "write", "keep_with_heartbeat")],
   "🔴 only collect.write makes a heartbeat, from whichever module calls it (so §4a's list is "
   "every heartbeat file there is)")
_kp = os.path.join(TMP, "keepers")
os.makedirs(_kp)
with open(os.path.join(_kp, "other.py"), "w", encoding="utf-8") as fh:
    fh.write("import collect, freshness as F\n\ndef save(p, d):\n    return F.keep_with_heartbeat(p, d)\n\n"
             "def put(p, d):\n    collect.write(p, d, compress=True, heartbeat=True)\n\n"
             "def own(p, d):\n    mywrite(p, d, heartbeat=True)\n\n"
             "def pos(p, d):\n    collect.write(p, d, True, heartbeat=True)\n\n"
             "def var(p, d, gz):\n    collect.write(p, d, compress=gz, heartbeat=True)\n")
eq(sorted(keepers(_kp)), [("other.py", "own", "heartbeat="), ("other.py", "pos", "heartbeat="),
                          ("other.py", "save", "keep_with_heartbeat"), ("other.py", "var", "heartbeat=")],
   "   (planted) a module keeping its own gzip, either way, is flagged, and so is a collect.write "
   "heartbeat §4a cannot list (a positional or computed compress); §4a's own form is listed there")

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

def _envs(tree):
    """{id(call): {name: value}}: the module's assignments, then the innermost
    enclosing function's on top (as `_tail` resolves a local)."""
    mod = {t.id: st.value for st in tree.body if isinstance(st, ast.Assign)
           for t in st.targets if isinstance(t, ast.Name)}
    out = {id(n): mod for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        env = dict(mod, **{t.id: n.value for n in ast.walk(fn) if isinstance(n, ast.Assign)
                           for t in n.targets if isinstance(t, ast.Name)})
        out.update({id(n): env for n in ast.walk(fn) if isinstance(n, ast.Call)})
    return out


def path_of(node, env, depth=0):
    """The path an expression spells, '*' for any part it cannot know: literals,
    f-strings, os.path.join, `+`, `%` and names (module, then function)."""
    if depth > 8:
        return "*"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        out = node.value
    elif isinstance(node, ast.JoinedStr):
        out = "".join(path_of(v.value if isinstance(v, ast.FormattedValue) else v, env, depth + 1)
                      for v in node.values)
    elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "join":
        out = "/".join(path_of(a, env, depth + 1) for a in node.args)
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        out = path_of(node.left, env, depth + 1) + path_of(node.right, env, depth + 1)
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) \
            and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
        out = re.sub(r"%[sd]", "*", node.left.value)
    elif isinstance(node, ast.Name) and node.id in env and env[node.id] is not node:
        out = path_of(env[node.id], env, depth + 1)
    else:
        out = "*"
    return re.sub(r"/+", "/", out.replace("\\", "/"))


_HB_RX = re.compile(r"(^|/)latest/(%s)$" % "|".join(re.escape(h) for h in HEARTBEAT))
# `[2026-11-10]` and a league's data/<lg>(/latest): its dossiers, game lines and record-detail;
#    `[review]` a league spelled as a variable (`*`, path_of's unknown) too
_TREE_RX = re.compile(r"(^|/)data(/(nfl|ncaaf|\*))?(/latest)?/?$")


def copies(paths):
    """-> (copytree calls whose source carries MLB's data/latest, single copies of a
    heartbeat file out of a latest/ path), each "file:line". `[2026-10-28, review]`
    Paths are RESOLVED (literal, f-string, join, a name): the first form saw only
    `os.path.join(..., 'latest', '<file>')`. ~~⚠️ A football data/<lg> copy carries no
    heartbeat file yet: widening is the football follow-up.~~ `[2026-11-10]` it does now."""
    trees, singles = [], []
    for _t in paths:
        tree = ast.parse(open(_t, encoding="utf-8").read())
        envs = _envs(tree)
        for _n in ast.walk(tree):
            if not (isinstance(_n, ast.Call) and _n.args):
                continue
            name = getattr(_n.func, "attr", None) or getattr(_n.func, "id", None)
            src = path_of(_n.args[0], envs.get(id(_n), {}))
            if name == "copytree" and _TREE_RX.search(src):
                trees.append("%s:%d" % (os.path.basename(_t), _n.lineno))
            if name in ("copy", "copy2", "copyfile") and _HB_RX.search(src):
                singles.append("%s:%d" % (os.path.basename(_t), _n.lineno))
    return trees, singles


_trees, _singles = copies(sorted(glob.glob(os.path.join(ROOT, "test_*.py"))))
eq(_trees, [], "🔴 no test copies a latest/ directory around tcheck.copy_latest")
eq(_singles, [], "🔴 no test copies one heartbeat file out of latest/ without its heartbeat")
with open(os.path.join(_pl, "test_bad.py"), "w", encoding="utf-8") as fh:
    fh.write("import os, shutil\n"
             "ROOT = os.path.dirname(os.path.abspath(__file__))\n"
             "LATEST = os.path.join(ROOT, 'data', 'latest')\n"
             "shutil.copy(os.path.join('data', 'latest', 'hitters.json.gz'), 'x')\n"
             "shutil.copy('data/latest/hitters.json.gz', 'x')\n"
             "shutil.copy2(f'{ROOT}/data/latest/pitchers.json.gz', 'x')\n"
             "shutil.copy(os.path.join(LATEST, 'scores.json.gz'), 'y')\n"
             "shutil.copytree(LATEST, 'z')\n"
             "shutil.copytree('data', 'w')\n"
             "shutil.copytree(os.path.join(ROOT, 'data', 'nfl'), 'v')\n"
             "shutil.copy(os.path.join(ROOT, 'tmp', 'hitters.json.gz'), 'u')\n"
             "shutil.copytree(os.path.join(ROOT, 'data', 'ncaaf', 'latest'), 's')\n"
             "shutil.copy(os.path.join(ROOT, 'data', 'nfl', 'latest', 'dossiers.json.gz'), 't')\n"
             "shutil.copytree(os.path.join(ROOT, 'data', 'nfl', '2026-11-10'), 'r')\n"
             "shutil.copytree(os.path.join(ROOT, 'data', lg), 'q')\n")
eq(copies([os.path.join(_pl, "test_bad.py")]),
   (["test_bad.py:8", "test_bad.py:9", "test_bad.py:10", "test_bad.py:12", "test_bad.py:15"],
    ["test_bad.py:4", "test_bad.py:5", "test_bad.py:6", "test_bad.py:7", "test_bad.py:13"]),
   "   (planted) every spelling is flagged: a join, a literal, an f-string, a LATEST name, a copy of "
   "data/; `[2026-11-10]` a football data/<lg> tree (its league literal or a variable), its latest/ "
   "and one of its heartbeat files too (~~are not~~); a file outside latest/ and a league's dated "
   "folder are not")

# ══════════════════════════════════════════════════════════════════════
section("4e. THE PAGE NEVER READS A HEARTBEAT FILE'S STAMP")
# ══════════════════════════════════════════════════════════════════════
# A page that printed a heartbeat file's own stamp would show the last CHANGE, not the
# last pull; it must read the time from a plain file (freshness.json) instead.
# `[2026-10-28, review]` EVERY stamp read on the page, by (top-level function,
# receiver), is named here with the file it reads; a new one is red until it is
# reasoned. (The first census saw only a variable filled straight from a literal
# fetch, so `D.built_at` after `const D = await loadRecordDetail()` passed.)
import jsblock as J  # noqa: E402

PAGE_STAMP_READS = {
    ("renderScores", "BOARD"): "data/latest/board.json (gamelines)",
    ("renderOdds", "BOARD"): "data/latest/board.json",
    ("<top>", "BOARD"): "data/latest/board.json (the refresh loop and the board's key)",
    ("<top>", "FRESH"): "data/latest/freshness.json (the refresh loop)",
    ("renderRecord", "R"): "data/latest/record.json (RECORD)",
    ("renderNews", "N"): "data/latest/news.json",
    ("fbOdds", "B"): "data/<lg>/latest/board.json (fbBoardLoad)",
    ("fbScores", "doc"): "data/<lg>/latest/schedule-<season>.json.gz (fbSchedLoad)",
    ("fbProps", "B"): "data/<lg>/latest/props.json.gz (fbPropsLoad)",
    ("fbRecord", "R"): "data/<lg>/latest/record.json (fbRecordLoad)",
    ("fbNews", "N"): "data/<lg>/latest/news.json (fbNewsLoad)",
    ("renderFootball", "doc"): "the football Trends file (fbLoad, fbPath)",
}
_PAGE_DIR = tempfile.mkdtemp(dir=TMP)


def page_reads(text):
    """-> ({(top-level function, receiver)} of every stamp read in the page's code,
    whether it ever fetches a .beat.json). Comments do not count."""
    code = J.strip_js(text)
    p = os.path.join(_PAGE_DIR, "page-%d.html" % len(os.listdir(_PAGE_DIR)))
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(code)
    spans = [(code.find(b), code.find(b) + len(b), n) for n, b in J.top_level_blocks(p).items()]
    rx = re.compile(r"(\)|[A-Za-z_$][\w$]*)\s*\??\.\s*(?:%s)\b|([A-Za-z_$][\w$]*)\s*\[\s*['\"](?:%s)['\"]\s*\]"
                    % ("|".join(F.STAMP_FIELDS), "|".join(F.STAMP_FIELDS)))
    reads = {(next((n for a, b, n in spans if a <= m.start() < b), "<top>"), m.group(1) or m.group(2))
             for m in rx.finditer(code)}
    return reads, ".beat.json" in code


_page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
_reads, _beat = page_reads(_page)
eq(sorted(_reads), sorted(PAGE_STAMP_READS),
   "🔴 every stamp read on the page is named, with the file it reads (a new one is red until it is)")
eq([v for v in PAGE_STAMP_READS.values() if any(h in v for h in HEARTBEAT)], [],
   "🔴 ...and none of them is a heartbeat file's")
eq(_beat, False, "   the page never fetches a .beat.json")
_planted = page_reads(_page + "\nasync function zzPlant(){\n  const D = await loadRecordDetail();\n"
                      "  return D.built_at + (await jgetGz('data/latest/hitters.json.gz')).pulled_at;\n}\n")[0]
eq(sorted(_planted - set(PAGE_STAMP_READS)), [("zzPlant", ")"), ("zzPlant", "D")],
   "   (planted) a stamp read through a loader, and one off an inline fetch, are flagged")

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
