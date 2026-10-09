#!/usr/bin/env python3
"""THE PROPS MODEL SETS THE FOOTBALL CARD'S CONFIDENCE. `[Sam, 2026-10-09]`

"Where fb_props_model prices a prop on the card ... the row's confidence is the
model's probability and the card ranks by it. A prop it does not price keeps the
player's own rate. The data keeps which one each row used." Planted trees pinned
to the real clock; nothing here reads the live data tree.
  1. A priced prop takes the model's %, ranked by it; an unpriced one the record.
  2. A props model that priced an older board falls back: the record, this build.
  3. No football row prints a caveat sentence: its one sentence is the record at
     the line, this season first.
  4. The Track Record's method is new from the switch, record-only builds too.
  5. The props model is built before the card, from the board the card reads.
  6. The agreement label still compares the RECORD with the model (Sam's choice).
  7. The page prints a football MODEL row's market, never "Outs".
  8. A failed name check strips the records and keeps the model's % (Sam's choice).

# @vacuity 🔴 a priced prop takes the model's %
#   file: card_fb.py
#   find:                 if _mp is not None:
#   with:                 if False:
#
# @vacuity 🔴 ...and an unpriced one keeps the record: the exact player, line and side
#   file: card_fb.py
#   find:     return (gid, who, mk, None if (line is None or mk == "player_anytime_td") else float(line), side)
#   with:     return (gid, mk, side)
#
# @vacuity 🔴 the card ranks by it
#   file: card_fb.py
#   find:     rows.sort(key=lambda r: (r.get("confidence") is None,
#   with:     rows.sort(key=lambda r: (-(r.get("rate") or 0), r.get("confidence") is None,
#
# @vacuity 🔴 a props model that priced an older board falls back to the record
#   file: card_fb.py
#   find:     if not B.get("pulled_at") or M.get("board_pulled_at") != B.get("pulled_at"):
#   with:     if not B.get("pulled_at"):
#
# @vacuity 🔴 the row's one sentence is the record, this season first
#   file: card_fb.py
#   find:     recs = ([(detail["h26"], detail["n26"], CUR_SEASON), (detail["h25"], detail["n25"], season)]
#   with:     recs = ([(detail["h25"], detail["n25"], season), (detail["h26"], detail["n26"], CUR_SEASON)]
#
# @vacuity 🔴 ...and no caveat sentence comes back
#   file: card_fb.py
#   find:     return [f"<b>{who}</b> {did} in {rec}, {when}."]
#   with:     return [f"<b>{who}</b> {did} in {rec}, {when}.", "This is his own record from last season, not a forecast."]
#
# @vacuity 🔴 the Track Record starts a new method from the switch
#   file: card_fb.py
#   find:                         else CARD_METHOD) + METHOD_PROPS_MODEL,
#   with:                         else CARD_METHOD),
#
# @vacuity 🔴 the props model is built before the card
#   file: collect.py
#   find:         _fpm.build(LEAGUE)
#   with:         pass
#
# @vacuity 🔴 ...stamped with the board it priced
#   file: fb_props_model.py
#   find:     doc["board_pulled_at"] = B.get("pulled_at")
#   with:     doc["board_pulled_at"] = None
#
# @vacuity 🔴 ...every book the board keeps, not only the best
#   file: fb_props_model.py
#   find:             for b, q in (sd.get("books") or {}).items():
#   with:             for b, q in list((sd.get("books") or {}).items())[:1]:
#
# @vacuity 🔴 the agreement label compares the record with the model
#   file: fb_agreement.py
#   find:                   "card_p": r.get("rate") if r.get("confidence_basis") == "MODEL" else r["confidence"],
#   with:                   "card_p": r["confidence"],
#
# @vacuity 🔴 the page prints a football MODEL row's market, never "Outs"
#   file: index.html
#   find:   const unit = isH || gl || p.kind === 'fb' ? p.market_label
#   with:   const unit = isH || gl ? p.market_label
#
# @vacuity 🔴 a failed name check keeps the model's %
#   file: card_fb.py
#   find:                 if r.get("confidence_basis") == "MODEL":
#   with:                 if False:
"""
import atexit
import datetime
import gzip
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
from tcheck import ck, eq, section  # noqa: E402
from jsblock import js_block  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime.now(UTC).replace(second=0, microsecond=0)
ISO = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
PULLED = ISO(NOW - datetime.timedelta(hours=1))
MK = "player_receptions"
TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])


def side(px):
    return {"price": px, "book": "fanduel", "n_books": 3, "link": None, "books": {
        "hardrockbet": {"price": px - 5, "pulled_at": PULLED[:16] + "Z"},
        "fanduel": {"price": px, "pulled_at": PULLED[:16] + "Z"},
        "draftkings": {"price": px - 10, "pulled_at": PULLED[:16] + "Z"}}}


BOARD = {"pulled_at": PULLED, "games": [{
    "id": "g1", "away": "A", "home": "H", "commence": ISO(NOW + datetime.timedelta(days=2)),
    "props": [{"player": who, "market": MK, "line": 3.5, "sides": {"over": side(-110)}}
              for who in ("Model Guy", "Record Guy")]}]}
# The model prices Model Guy's over at 3.5, and Record Guy only at a line the board lacks.
RATED = [{"game_id": "g1", "player": "Model Guy", "market": MK, "line": 3.5, "side": "over", "p": 41.6},
         {"game_id": "g1", "player": "Record Guy", "market": MK, "line": 4.5, "side": "over", "p": 30.0}]


def games(season, hits, n):
    d0 = datetime.date(2025, 9, 7) if season == 2025 else (NOW - datetime.timedelta(days=40)).date()
    return [{"d": (d0 + datetime.timedelta(days=7 * i)).isoformat(), "snap_pct": 0.9, "team": "H",
             "rec": 5 if i < hits else 1, "rec_yds": 0, "rush_yds": 0, "rec_td": 0, "rush_td": 0,
             "pass_yds": 0, "pass_td": 0} for i in range(n)]


def card(model_board_at, board=BOARD):
    """card_fb.main() on a planted tree whose props model priced `model_board_at`."""
    t = tempfile.mkdtemp(prefix="pmconf-")
    TREES.append(t)
    lat = os.path.join(t, "data", "nfl", "latest")
    os.makedirs(lat)
    for name, doc in (("props.json.gz", board),
                      ("players-2025.json.gz", {"season": 2025, "players": {
                          "1": {"name": "Model Guy", "pos": "WR", "g": games(2025, 10, 10)},
                          "2": {"name": "Record Guy", "pos": "WR", "g": games(2025, 6, 10)}}}),
                      ("players-2026.json.gz", {"season": 2026, "players": {
                          "1": {"name": "Model Guy", "pos": "WR", "g": games(2026, 4, 4)},
                          "2": {"name": "Record Guy", "pos": "WR", "g": games(2026, 2, 4)}}})):
        with gzip.open(os.path.join(lat, name), "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    with open(os.path.join(lat, "fb-props-model.json"), "w", encoding="utf-8") as fh:
        json.dump({"board_pulled_at": model_board_at, "rated": RATED}, fh)
    cwd = os.getcwd()
    try:
        os.chdir(t)
        sys.modules.pop("card_fb", None)
        cf = importlib.import_module("card_fb")
        cf.main()
        with open(os.path.join("picks", "fb-nfl-latest.json"), encoding="utf-8") as fh:
            return json.load(fh), cf
    finally:
        os.chdir(cwd)
        sys.modules.pop("card_fb", None)


DOC, CF = card(PULLED)
STALE, _ = card(ISO(NOW - datetime.timedelta(hours=4)))
P = {r["player"]: r for r in DOC.get("picks") or []}
M_, R_ = P.get("Model Guy") or {}, P.get("Record Guy") or {}

section("1. 🔴 A PRICED PROP TAKES THE MODEL'S %, RANKED BY IT; AN UNPRICED ONE THE RECORD")
eq((M_.get("confidence"), M_.get("model_p"), M_.get("confidence_basis")), (42, 41.6, "MODEL"),
   "🔴 Model Guy's over is priced by the model: 41.6% shows as 42, labelled MODEL")
eq((M_.get("rate"), M_.get("record"), M_.get("break_even"), M_.get("edge")), (71, "14 of 14", 52.4, -10.4),
   "   ...his own record stays in the data, and the edge is the model's % less the break-even")
eq((R_.get("confidence"), R_.get("confidence_basis"), "model_p" in R_), (52, "RECORD", False),
   "🔴 Record Guy's 3.5 is not priced by the model (only his 4.5 is): his own rate, labelled RECORD")
eq([r["player"] for r in DOC.get("picks") or []], ["Record Guy", "Model Guy"],
   "🔴 the card ranks by it: the model's 42 sits under the record's 52")

section("2. 🔴 A PROPS MODEL THAT PRICED AN OLDER BOARD FALLS BACK TO THE RECORD")
eq({r["player"]: (r.get("confidence"), r.get("confidence_basis"), "model_p" in r)
    for r in STALE.get("picks") or []},
   {"Model Guy": (71, "RECORD", False), "Record Guy": (52, "RECORD", False)},
   "🔴 the model priced the board pulled 4 hours earlier: every row is the record this build")
eq((DOC.get("props_model_used"), STALE.get("props_model_used")), (True, False),
   "   ...and the card says which build used it")

section("3. 🔴 NO FOOTBALL ROW PRINTS A CAVEAT SENTENCE")
_snaps = ", when he played at least half the snaps."
eq(M_.get("why"), ["<b>Model Guy</b> went over 3.5 rec in <b>4 of 4 games</b> in 2026 and 10 of 10 in 2025"
                   + _snaps], "🔴 the row's one sentence is his record at the line, this season first")
_rows = (DOC.get("picks") or []) + (STALE.get("picks") or [])
_bad = [(r["player"], s) for r in _rows for s in r.get("why") or []
        if len(r.get("why") or []) != 1 or any(w in s for w in (
            "forecast", "never faced", "prediction", "small sample", "averaged", "model", "box scores"))]
_bad += [(r["player"], k) for r in _rows for k in ("confidence_note", "projection_note", "basis")
         if any(w in (r.get(k) or "") for w in ("no football model", "not a forecast", "no model"))]
ck(bool(_rows) and not _bad, "🔴 every row, priced or not: one sentence, and no caveat in it or its notes",
   str(_bad[:3]))

section("4. 🔴 THE TRACK RECORD STARTS A NEW METHOD FROM THE SWITCH")
eq((DOC.get("card_method"), STALE.get("card_method")), (CF.METHOD_FIXED + "+props-model",) * 2,
   "🔴 every card from the switch carries the new method, a record-only build included, so the "
   "old bands stay as they were graded")

section("5. 🔴 THE PROPS MODEL IS BUILT BEFORE THE CARD, FROM THE BOARD THE CARD READS")
import collect as C  # noqa: E402
_calls, _old = [], (sys.modules.get("fb_props_model"), subprocess.run, C.LEAGUE)
try:
    sys.modules["fb_props_model"] = types.SimpleNamespace(build=lambda lg: _calls.append(("model", lg)))
    subprocess.run = lambda cmd, **k: (_calls.append(("card", cmd[-1])),
                                       types.SimpleNamespace(returncode=0, stdout="", stderr=""))[1]
    C.LEAGUE = "nfl"
    C.build_card_fb()
finally:
    subprocess.run, C.LEAGUE = _old[1], _old[2]
    if _old[0] is None:
        sys.modules.pop("fb_props_model", None)
    else:
        sys.modules["fb_props_model"] = _old[0]
eq(_calls, [("model", "nfl"), ("card", "card_fb.py")],
   "🔴 build_card_fb builds the props model first, on both card paths (the props pull and card-fb)")
import fb_props_model as FPM  # noqa: E402
_r = FPM.rungs_of("nfl", FPM.board_event(BOARD["games"][0])).get(("Model Guy", MK, 3.5)) or {}
eq((sorted(_r.get("books") or {}), (_r.get("best") or {}).get("over")),
   (["draftkings", "fanduel", "hardrockbet"], (-110, "fanduel")),
   "🔴 the model prices the board itself: every book's latest price, and the board's best")
_t = tempfile.mkdtemp(prefix="pmconf-build-")
TREES.append(_t)
os.makedirs(os.path.join(_t, "data", "nfl", "latest"))
with gzip.open(os.path.join(_t, "data", "nfl", "latest", "props.json.gz"), "wt", encoding="utf-8") as fh:
    json.dump(BOARD, fh)
_o = (FPM.walk_forward, FPM.current_picks, FPM.log)
try:
    FPM.walk_forward = lambda *a, **k: {"picks": [], "graded": [], "weeks": [], "stage2_weeks": {},
                                        "card_season": 2025, "card_seasons": {}}
    FPM.current_picks = lambda lg, wf, root=None, now=None, rated=None, board=None: (
        rated.extend(RATED) if (board or {}).get("pulled_at") == PULLED else None) or []
    FPM.log = lambda m: None
    _doc = FPM.build("nfl", root=_t, out=os.path.join(_t, "fbp.json"))
finally:
    FPM.walk_forward, FPM.current_picks, FPM.log = _o
eq((_doc.get("board_pulled_at"), len(_doc.get("rated") or [])), (PULLED, 2),
   "🔴 ...and fb-props-model.json is stamped with the board it priced, which the card checks")

section("6. 🔴 THE AGREEMENT LABEL STILL COMPARES THE RECORD WITH THE MODEL")
import fb_agreement as AG  # noqa: E402
_ag = AG.rows({"picks": [M_]}, {"rated": RATED})
eq([(a["card_p"], a["model_p"], a["label"]) for a in _ag], [(71, 41.6, "SPLIT")],
   "🔴 Sam's choice: the card's side is his record (71), not the model's own 42, so a priced "
   "row is not AGREE by construction")

section("7. 🔴 THE PAGE PRINTS A FOOTBALL MODEL ROW'S MARKET, NEVER \"Outs\"")
PAGE = os.path.join(ROOT, "index.html")
_el = next(l for l in open(PAGE, encoding="utf-8").read().splitlines() if l.startswith("const el = "))
DRIVER = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const text = n => (n.innerHTML || '') + ' ' + (n.kids || []).map(text).join(' ');
function node(){ return {className: '', innerHTML: '', kids: [],
  append(...k){ this.kids.push(...k); }, insertAdjacentHTML(_, h){ this.kids.push({innerHTML: h}); } }; }
const document = {createElement: () => node()};
const stub = () => '';
const pickCard = new Function('document', 'confClass', 'headUrl', 'projChip', 'mark', 'ab', 'sgn',
  'bookChip', 'betControl', 'betLink', 'fbMark', 'fbAb', 'FBTEAMS', 'LEAGUE',
  S.el + '\n' + S.pc + '\nreturn pickCard;')(document, stub, stub, stub, stub, stub, String,
  stub, stub, stub, stub, stub, {}, 'nfl');
process.stdout.write(JSON.stringify(text(pickCard(S.row)).replace(/\s+/g, ' ')));
"""
_d = tempfile.mkdtemp(prefix="pmconf-js-")
TREES.append(_d)
with open(os.path.join(_d, "d.js"), "w", encoding="utf-8") as fh:
    fh.write(DRIVER)
with open(os.path.join(_d, "d.json"), "w", encoding="utf-8") as fh:
    json.dump({"el": _el, "pc": js_block("pickCard", PAGE), "row": M_}, fh)
_js = subprocess.run(["node", os.path.join(_d, "d.js"), os.path.join(_d, "d.json")],
                     capture_output=True, text=True, timeout=300)
HTML = json.loads(_js.stdout) if _js.returncode == 0 else ""
ck(_js.returncode == 0 and "Over 3.5 Receptions" in HTML and "Outs" not in HTML,
   "🔴 Model Guy's row reads \"Over 3.5 Receptions\" with its 42", (_js.stderr or "")[-200:] + HTML[:200])

section("8. 🔴 A FAILED NAME CHECK STRIPS THE RECORDS AND KEEPS THE MODEL'S %")
# Three more names no log holds: 2 of 5 match, under the 60% bar.
WEAK = dict(BOARD, games=[dict(BOARD["games"][0], props=BOARD["games"][0]["props"] + [
    {"player": "Nobody %d" % i, "market": MK, "line": 3.5, "sides": {"over": side(-110)}} for i in range(3)])])
_w, _ = card(PULLED, WEAK)
_W = {r["player"]: r for r in _w.get("picks") or []}
eq((_w.get("name_match_rate"), (_W.get("Model Guy") or {}).get("confidence"),
    (_W.get("Model Guy") or {}).get("confidence_basis"), (_W.get("Model Guy") or {}).get("why")),
   (0.4, 42, "MODEL", []), "🔴 Sam's choice: Model Guy keeps the model's 42 (the model matched him "
   "itself), with no record sentence")
eq(((_W.get("Record Guy") or {}).get("confidence"), (_W.get("Record Guy") or {}).get("confidence_basis")),
   (None, "MARKET"), "   ...and Record Guy's record, from the failed join, is withheld")
