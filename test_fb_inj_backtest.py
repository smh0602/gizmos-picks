#!/usr/bin/env python3
"""test_fb_inj_backtest.py — THE INJURY BAR'S RUNNER, AND WHICH LEAGUE'S READINGS A ROW GETS.

`[Sam, 2026-10-17]` NFL injuries: "In the sim, backtest-gated"; college: "use the college injury
source as long as it's accurate and up to date, we wouldn't want misinformation ruining our bets"
(research/cfb_injuries_design.md §4: the same bar). It asks:
  1. `fb_inj_backtest.passes` is the bar: log loss with <= without AND closing return with >=
     without, both, and agrees with test_fb_sim.py §3's reading of every recorded entry.
  2. `fb_inj_backtest.record` writes a league's entry ONCE and refuses to overwrite it.
  3. `fb_model.injury_readings`: a college row gets the conference reports' readings
     (`cfb_injuries.attach`), never T69 IN's, which read data/nfl; an NFL row gets IN's.

PLANTED DATA ONLY: the record file is a temp copy; the attach functions are stand-ins.

# @vacuity 🔴 the bar needs the log loss to hold
#   file: fb_inj_backtest.py
#   find: return ll["with"] <= ll["without"] and cr["with"] >= cr["without"]
#   with: return cr["with"] >= cr["without"]
#
# @vacuity 🔴 ...and the closing return to hold
#   file: fb_inj_backtest.py
#   find: return ll["with"] <= ll["without"] and cr["with"] >= cr["without"]
#   with: return ll["with"] <= ll["without"]
#
# @vacuity 🔴 a missing number never passes
#   file: fb_inj_backtest.py
#   find: if None in (ll.get("with"), ll.get("without"), cr.get("with"), cr.get("without")):
#   with: if False:
#
# @vacuity ⛔ a recorded entry is never overwritten: the bar is run once
#   file: fb_inj_backtest.py
#   find: if lg in inj:
#   with: if False:
#
# @vacuity ⛔ a college row never gets T69 IN's NFL readings
#   file: fb_model.py
#   find:     if lg == "ncaaf":
#   with:     if False:
#
# @vacuity 🔴 an NFL row gets T69 IN's readings
#   file: fb_model.py
#   find:     return fb_challengers.attach("IN", lg, rows, root)
#   with:     return rows
#
# @vacuity ⛔ [2026-10-17] a league already recorded is never measured again
#   file: fb_inj_backtest.py
#   find:     if lg in rec:
#   with:     if False:
#
# @vacuity ⛔ [2026-10-17] the FIRST measured result stands: never a second measurement
#   file: fb_inj_backtest.py
#   find:     if prev and prev.get("state") == "measured" and prev.get("entry"):
#   with:     if False:
#
# @vacuity ⛔ [2026-10-17] it waits for the data the bar needs
#   file: fb_inj_backtest.py
#   find:         if missing:
#   with:         if False:
#
# @vacuity ⛔ [2026-10-17] only a PASS switches injuries on in the branch
#   file: fb_inj_backtest.py
#   find:         if st["passes"]:
#   with:         if True:
#
# @vacuity ⛔ [2026-10-17] no fit, no test: a measurement with no injury fit is never recorded
#   file: fb_inj_backtest.py
#   find:         if not entry.get("fitted_last") or not entry.get("questions_moved"):
#   with:         if not entry.get("questions_moved"):
#
# @vacuity ⛔ [2026-10-17, review] an archive file is not a season: every reading conference must be in it
#   file: fb_inj_backtest.py
#   find:             if CI.night_before(s, c) and (c not in have or ((owed.get(str(s)) or {}).get(c) or {}).get("due")):
#   with:             if False:
#
# @vacuity ⛔ [2026-10-17, review] a result already on a branch is never measured again
#   file: fb_inj_backtest.py
#   find:         if branch:
#   with:         if False:
#
# @vacuity ⛔ [2026-10-17, review] git that cannot answer never reads as "no branch"
#   file: fb_refit.py
#   find:     if r.returncode != 0:
#   with:     if False:
#
# @vacuity ⛔ [2026-10-17, review] a fit that moved no scored question is not a test
#   file: fb_inj_backtest.py
#   find:         if not entry.get("fitted_last") or not entry.get("questions_moved"):
#   with:         if not entry.get("fitted_last"):
#
# @vacuity ⛔ [2026-10-17, review] the bar is decided on the exact numbers
#   file: fb_inj_backtest.py
#   find:     ex = entry.get("exact") or {}
#   with:     ex = {}
#
# @vacuity 🔴 [2026-10-17] the weekly job keeps the result in fb-refit.json
#   file: fb_refit.py
#   find:             doc["injury_backtest"] = fb_inj_backtest.auto(lg, root, now, run, prev=_was)
#   with:             doc["injury_backtest"] = None
#
# @vacuity 🔴 [2026-10-17] the Monday email names a waiting injury branch
#   file: status.py
#   find:     if st.get("state") != "measured" or not st.get("branch"):
#   with:     if True:
#
# @vacuity 🔴 [2026-10-26] once main holds the entry (Sam merged), the email stops asking him to merge
#   file: status.py
#   find:     if recorded:
#   with:     if False:
#
# @vacuity 🔴 [2026-10-26] ...decided by the tree's own research/fb_sim_backtest.json, in the email itself
#   file: status.py
#   find:         doc, name, injury_recorded(root, d.split("/")[-1]))]
#   with:         doc, name, False)]
#
# @vacuity 🔴 [2026-10-26] a live build's moment reaches college's injury reading
#   file: fb_model.py
#   find:         return cfb_injuries.attach(rows, root, now=now, shown_at=shown)
#   with:         return cfb_injuries.attach(rows, root, shown_at=shown)
"""
import json
import os
import shutil
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "nfl")
import fb_inj_backtest as B  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

E = lambda llw, llo, crw, cro: {"logloss": {"with": llw, "without": llo},  # noqa: E731
                                "closing_return": {"with": crw, "without": cro}}

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE BAR: BOTH NUMBERS, EVERY TIME")
# ══════════════════════════════════════════════════════════════════════
ck("✅ both hold -> passes", B.passes(E(0.700, 0.701, 2.0, 1.0)))
ck("✅ ...ties pass (at most / at least)", B.passes(E(0.700, 0.700, 1.0, 1.0)))
ck("🔴 the log loss worse -> fails, however good the return (NFL's real case: .70281 v .70259, "
   "+3.92% v +1.85%)", not B.passes(E(0.70281, 0.70259, 3.92, 1.85)))
ck("🔴 the return worse -> fails, however good the log loss", not B.passes(E(0.690, 0.700, 1.0, 2.0)))
ck("🔴 a missing number never passes", not B.passes(E(None, 0.70, 2.0, 1.0))
   and not B.passes({"logloss": {"with": 0.6, "without": 0.7}}))
_rec = json.load(open(B.RECORD, encoding="utf-8"))
_tfs = {lg: v["logloss"]["with"] <= v["logloss"]["without"]
        and v["closing_return"]["with"] >= v["closing_return"]["without"]
        for lg, v in (_rec.get("injuries") or {}).items()}
eq({lg: B.passes(v) for lg, v in (_rec.get("injuries") or {}).items()}, _tfs,
   "✅ ...and it reads every recorded entry exactly as test_fb_sim.py §3 does")

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ A LEAGUE'S ENTRY IS RECORDED ONCE")
# ══════════════════════════════════════════════════════════════════════
_t = tempfile.mkdtemp(prefix="injbt-")
try:
    _p = os.path.join(_t, "rec.json")
    json.dump({"run": "x", "injuries": {"nfl": E(0.7, 0.6, 1.0, 2.0)}}, open(_p, "w", encoding="utf-8"))
    _before = open(_p, encoding="utf-8").read()
    ck("⛔ an existing entry is refused", B.record("nfl", E(0.1, 0.9, 9.0, 0.0), _p) is False)
    eq(open(_p, encoding="utf-8").read(), _before, "⛔ ...and the file is untouched")
    ck("✅ a new league's entry is written", B.record("ncaaf", E(0.7, 0.71, 1.0, 0.5), _p) is True)
    _d = json.load(open(_p, encoding="utf-8"))
    eq((_d["injuries"]["ncaaf"]["logloss"], _d["run"], sorted(_d["injuries"])),
       ({"with": 0.7, "without": 0.71}, "x", ["ncaaf", "nfl"]), "✅ ...beside what was there")
    ck("⛔ ...and a second run of it is refused", B.record("ncaaf", E(0.1, 0.9, 9.0, 0.0), _p) is False)
finally:
    shutil.rmtree(_t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ EACH LEAGUE'S ROWS GET ITS OWN READINGS")
# ══════════════════════════════════════════════════════════════════════
import fb_challengers  # noqa: E402
import fb_model as FM  # noqa: E402

_calls = []
_fake = types.ModuleType("cfb_injuries")
# `[2026-10-26]` the stand-in takes the real signature's `now` (a live build's moment) and records it
# `[2026-10-26, review]` ...and `shown_at` (each played game's last pre-kickoff build, the record's)
_fake.attach = lambda rows, root=None, now=None, shown_at=None: _calls.append(
    ("college", len(rows), now, shown_at)) or rows
_empty = tempfile.mkdtemp(prefix="injbt-")          # ⛔ no ledger of production's is read
_saved_mod, _saved_in = sys.modules.get("cfb_injuries"), fb_challengers.attach
sys.modules["cfb_injuries"] = _fake
fb_challengers.attach = lambda name, lg, rows, root=None: _calls.append(("IN", lg)) or rows
try:
    FM.injury_readings("ncaaf", [{}, {}])
    _college = list(_calls)
    _calls.clear()
    FM.injury_readings("ncaaf", [{}], _empty, now="BUILD")
    _college_now = list(_calls)
    _calls.clear()
    FM.injury_readings("nfl", [{}])
    _nfl = list(_calls)
finally:
    fb_challengers.attach = _saved_in
    if _saved_mod is None:
        sys.modules.pop("cfb_injuries", None)
    else:
        sys.modules["cfb_injuries"] = _saved_mod
    shutil.rmtree(_empty, ignore_errors=True)
# `[2026-10-26]` ~~[("college", 2)]~~: the reading's moment is asked too (None: §3's tested 9:00 read)
eq(_college, [("college", 2, None, None)], "⛔ a college row gets the conference reports' readings, never T69 IN's "
   "(which read data/nfl: every college team would read zero), at §3's tested reading by default, and no "
   "ledger is read")
eq(_college_now, [("college", 1, "BUILD", {})],
   "🔴 [2026-10-26] ...and a live build's moment reaches college's reading (Sam: \"do 9am, 12pm, 7pm\"), with "
   "the ledger's shown moments (none in an empty tree)")
eq(_nfl, [("IN", "nfl")], "🔴 an NFL row gets T69 IN's readings")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 IT RUNS ITSELF: ONCE, WHEN ITS DATA IS STORED, ON A BRANCH FOR SAM")
# ══════════════════════════════════════════════════════════════════════
# `[Sam, 2026-10-17]` nothing recurring runs in Claude: the Monday fb-refit job calls `auto`.
import datetime  # noqa: E402

import fb_refit  # noqa: E402
import status as ST  # noqa: E402

NOW = datetime.datetime(2026, 10, 19, 9, 47, tzinfo=datetime.timezone.utc)
import re  # noqa: E402

import cfb_injuries as CI  # noqa: E402
# `[2026-10-17, review]` ⛔ the planted fb_model.py has college injuries OFF, whatever the live switch
#    says: on the branch a PASS pushes (ncaaf True), this test must still be green.
SRC = re.sub(r'^(INJURIES = \{[^\n]*"ncaaf": )True', r"\g<1>False",
             open(os.path.join(ROOT, "fb_model.py"), encoding="utf-8").read(), flags=re.M)


def tree(have_data=True, recorded=False, drop=None, due=None):
    """A planted tree: the record, fb_model.py, and (have_data) every file the bar needs, each
    archive holding every conference that gives a pick-time reading, except `drop`=(season, conf);
    `due`=(season, conf) is still owed a refresh in the probe."""
    t = tempfile.mkdtemp(prefix="injauto-")
    os.makedirs(os.path.join(t, "research"))
    rec = {"injuries": {"nfl": E(0.70281, 0.70259, 3.92, 1.85)}}
    if recorded:
        rec["injuries"]["ncaaf"] = E(0.71, 0.72, 1.0, 0.5)
    json.dump(rec, open(os.path.join(t, "research", "fb_sim_backtest.json"), "w", encoding="utf-8"))
    open(os.path.join(t, "fb_model.py"), "w", encoding="utf-8").write(SRC)
    if have_data:
        for s in (2025, 2026):
            for k in ("defense", "roster"):
                p = os.path.join(t, "data", "ncaaf", "latest", "%s-%d.json.gz" % (k, s))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "wb").close()
            confs = CI.HDI_LEGACY if s == CI.LEGACY_SEASON else CI.HDI_ARCHIVE
            p = CI.archive_path(s, t)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            import gzip as _gz
            with _gz.open(p, "wt", encoding="utf-8") as fh:
                json.dump({"conferences": {c: {"rows": []} for c in confs if (s, c) != drop}}, fh)
        pp = CI.probe_path(2026, t)
        os.makedirs(os.path.dirname(pp), exist_ok=True)
        json.dump({"archives": {str(due[0]): {due[1]: {"due": True}}} if due else {}},
                  open(pp, "w", encoding="utf-8"))
    return t


class _Done:
    def __init__(self, rc=0, out="", err=""):
        self.returncode, self.stdout, self.stderr = rc, out, err


def fake_git(branch=None, entry=None, broken=False):
    """`run` for fb_refit's git calls: origin holds `branch` (whose research/fb_sim_backtest.json
    records `entry` for college) or nothing; `broken`: git cannot answer at all."""
    def run(cmd, **kw):
        if broken:
            return _Done(128, "", "fatal: not a git repository")
        if cmd[1] == "ls-remote":
            return _Done(0, ("abc123\trefs/heads/%s\n" % branch) if branch else "")
        if cmd[1] == "fetch":
            return _Done(0)
        if cmd[1] == "show":
            return _Done(0, json.dumps({"injuries": {"ncaaf": entry} if entry else {}}))
        return _Done(1, "", "unexpected %s" % cmd)
    return run


GIT = fake_git()
_measured, _pushed = [], []


def fake_measure(entry):
    def m(lg, root=None):
        _measured.append(lg)
        return dict(entry)
    return m


def fake_push(fail=False):
    def push(prefix, branch, edit, message, root=None, run=None):
        if fail:
            raise RuntimeError("push refused")
        t = tempfile.mkdtemp(prefix="injbranch-")
        os.makedirs(os.path.join(t, "research"))
        shutil.copy(os.path.join(root, "research", "fb_sim_backtest.json"), os.path.join(t, "research"))
        shutil.copy(os.path.join(root, "fb_model.py"), t)
        edit(t)
        _pushed.append((prefix, branch, message,
                        json.load(open(os.path.join(t, "research", "fb_sim_backtest.json"), encoding="utf-8")),
                        [ln for ln in open(os.path.join(t, "fb_model.py"), encoding="utf-8").read().splitlines()
                         if ln.startswith("INJURIES = ")]))
        shutil.rmtree(t, ignore_errors=True)
        return branch, True
    return push


def fresh():
    _measured.clear()
    _pushed.clear()


_saved = (B.measure, fb_refit.push_change)
# a real fit that moved scored questions: the test can say something
_FIT = {"fitted_last": ["2026-10-12", [1.0, 0.2, 0.3]], "questions_moved": 640}
_PASS, _FAIL = dict(E(0.719, 0.720, -3.0, -3.5), **_FIT), dict(E(0.722, 0.720, -3.0, -3.5), **_FIT)
_trees = []
try:
    B.measure, fb_refit.push_change = fake_measure(_PASS), fake_push()
    _trees.append(tree(recorded=True))
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    ck("⛔ a league already recorded is never measured again",
       st["state"] == "recorded" and not _measured and not _pushed, str(st))
    st = B.auto("nfl", _trees[-1], NOW, run=GIT)
    ck("✅ ...the NFL's recorded FAIL reads as recorded, not passed",
       st["state"] == "recorded" and st["passes"] is False, str(st))

    _trees.append(tree(have_data=False))
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    ck("⛔ it waits while the data the bar needs is missing, and says which",
       st["state"] == "waiting" and "data/ncaaf/latest/defense-2025.json.gz" in st["missing"]
       and not _measured, str(st))
    _trees.append(tree(drop=(2025, "SEC")))
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    ck("⛔ [review] an archive file is not a season: 2025's archive without SEC waits, naming SEC",
       st["state"] == "waiting" and any(m.endswith("injury-archive-2025.json.gz#SEC") for m in st.get("missing", []))
       and not _measured, str(st))
    _trees.append(tree(due=(2026, "ACC")))
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    ck("⛔ [review] ...nor while a conference's archive is still owed a refresh (ACC 2026)",
       st["state"] == "waiting" and any(m.endswith("injury-archive-2026.json.gz#ACC") for m in st.get("missing", []))
       and not _measured, str(st))
    ck("✅ ...and a conference that gives no pick-time reading never blocks it (B10 2025: game day only)",
       not any("#B10" in m or "#CFP" in m for m in B.needed("ncaaf", _trees[-1], NOW)),
       str(B.needed("ncaaf", _trees[-1], NOW)))

    fresh()
    _trees.append(tree())
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    _p = _pushed[-1] if _pushed else (None,) * 5
    ck("🔴 with its data stored it measures ONCE and pushes ONE branch for Sam",
       st["state"] == "measured" and _measured == ["ncaaf"] and st.get("branch") == "fb/injuries-ncaaf-2026-10-19"
       and _p[0] == "fb/injuries-ncaaf-", str(st))
    eq(((_p[3] or {}).get("injuries", {}).get("ncaaf"), _p[4]),
       (_PASS, ['INJURIES = {"nfl": False, "ncaaf": True}']),
       "🔴 a PASS: the branch records the entry AND switches college injuries on")
    _again = B.auto("ncaaf", _trees[-1], NOW, run=GIT, prev=st)
    ck("⛔ the next week keeps the first result: no second measurement, no second branch",
       _measured == ["ncaaf"] and len(_pushed) == 1 and _again.get("entry") == _PASS, str(_again))

    fresh()
    _trees.append(tree())
    st = B.auto("ncaaf", _trees[-1], NOW, run=fake_git("fb/injuries-ncaaf-2026-10-12", _FAIL))
    ck("⛔ [review] last week's fb-refit.json lost but its branch on origin: the BRANCH's result stands "
       "(FAIL), never a second measurement and never a new branch",
       st["state"] == "measured" and st.get("entry") == _FAIL and st.get("passes") is False
       and st.get("branch") == "fb/injuries-ncaaf-2026-10-12" and not _measured and not _pushed, str(st))
    st = B.auto("ncaaf", _trees[-1], NOW, run=fake_git(broken=True))
    ck("⛔ [review] git cannot answer: it waits, never measures blind", st["state"] == "waiting"
       and "could not ask origin" in st.get("why", "") and not _measured and not _pushed, str(st))

    fresh()
    B.measure = fake_measure(dict(_PASS, fitted_last=None, rows_with_injury_reading=12))
    _trees.append(tree())
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    ck("⛔ no fit, no test: too few readings to size an injury ('with' would equal 'without' and pass "
       "while proving nothing) is not recorded and pushes nothing; it waits for next week",
       st["state"] == "waiting" and "too few injury readings" in st.get("why", "") and not _pushed, str(st))
    fresh()
    B.measure = fake_measure(dict(_PASS, questions_moved=0))
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    ck("⛔ [review] ...nor a fit only for weeks not yet played, which moves no scored question (a tie that "
       "would PASS)", st["state"] == "waiting" and not _pushed, str(st))

    fresh()
    B.measure = fake_measure(_FAIL)
    _trees.append(tree())
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    _p = _pushed[-1] if _pushed else (None,) * 5
    eq((st.get("passes"), (_p[3] or {}).get("injuries", {}).get("ncaaf"), _p[4]),
       (False, _FAIL, ['INJURIES = {"nfl": False, "ncaaf": False}']),
       "⛔ a FAIL: the branch only records it; college injuries stay off")

    fresh()
    _NEAR = dict(E(0.72088, 0.72088, -3.88, -3.88), **_FIT,
                 exact={"logloss": {"with": 0.7208843, "without": 0.7208801},
                        "closing_return": {"with": -3.884, "without": -3.880}})
    B.measure = fake_measure(_NEAR)
    _trees.append(tree())
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    _p = _pushed[-1] if _pushed else (None,) * 5
    ck("⛔ [review] decided on the EXACT numbers: a slightly worse 'with' that ties after rounding FAILS, "
       "and injuries stay off", B.passes(_NEAR) is False and st.get("passes") is False
       and _p[4] == ['INJURIES = {"nfl": False, "ncaaf": False}'], str(st))

    fresh()
    B.measure, fb_refit.push_change = fake_measure(_PASS), fake_push(fail=True)
    _trees.append(tree())
    st = B.auto("ncaaf", _trees[-1], NOW, run=GIT)
    ck("✅ a refused push keeps the measured result, and says why, for the next week to push",
       st["state"] == "measured" and "branch" not in st and "push refused" in st.get("branch_error", ""), str(st))
    fb_refit.push_change = fake_push()
    st2 = B.auto("ncaaf", _trees[-1], NOW, run=GIT, prev=st)
    ck("✅ ...which pushes it without measuring again",
       _measured == ["ncaaf"] and st2.get("branch") and "branch_error" not in st2, str(st2))
finally:
    B.measure, fb_refit.push_change = _saved
    for t in _trees:
        shutil.rmtree(t, ignore_errors=True)

# ── the weekly job keeps it, and the Monday email names it ────────────
_saved = (fb_refit.league, B.auto)
_seen = []
fb_refit.league = lambda lg, root=None, now=None, prev=None, added=None, rows=None: {"league": lg,
                                                                                    "challengers": []}
B.auto = lambda lg, root=None, now=None, run=None, prev=None: _seen.append((lg, prev)) or {"state": "waiting",
                                                                                           "lg": lg}
_t = tempfile.mkdtemp(prefix="injweekly-")
try:
    for lg in ("nfl", "ncaaf"):
        os.makedirs(os.path.join(_t, "data", lg, "latest"))
    json.dump({"injury_backtest": {"state": "measured", "x": 1}},
              open(os.path.join(_t, "data", "ncaaf", "latest", "fb-refit.json"), "w", encoding="utf-8"))
    fb_refit.weekly(root=_t, now=NOW)
    _docs = {lg: json.load(open(os.path.join(_t, "data", lg, "latest", "fb-refit.json"), encoding="utf-8"))
             for lg in ("nfl", "ncaaf")}
finally:
    fb_refit.league, B.auto = _saved
    shutil.rmtree(_t, ignore_errors=True)
eq({lg: d.get("injury_backtest") for lg, d in _docs.items()},
   {"nfl": {"state": "waiting", "lg": "nfl"}, "ncaaf": {"state": "waiting", "lg": "ncaaf"}},
   "🔴 the Monday job keeps each league's injury state in its fb-refit.json")
eq(dict(_seen).get("ncaaf"), {"state": "measured", "x": 1},
   "⛔ ...handing back last week's state, so a measured result is never measured again")

_w = ST.injury_branch({"injury_backtest": {"state": "measured", "branch": "fb/injuries-ncaaf-2026-10-19",
                                           "passes": True, "entry": dict(_PASS, questions=900)}}, "College")
ck("🔴 the Monday email names a waiting injury branch, its result and its clicks",
   len(_w) == 1 and "PASSED" in _w[0][0] and "switches them on" in _w[0][0]
   and "compare/main...fb/injuries-ncaaf-2026-10-19" in _w[0][1][0], str(_w))
ck("✅ ...and says nothing while it waits for data or once it is recorded",
   ST.injury_branch({"injury_backtest": {"state": "waiting"}}, "College") == []
   and ST.injury_branch({"injury_backtest": {"state": "recorded"}}, "College") == [])

# 🔴 `[2026-10-26]` ONCE SAM MERGED THE BRANCH, THE EMAIL STOPS ASKING HIM TO. fb-refit.json still
#    says "measured" (with the branch) until the next Monday's job rewrites it, and the email read
#    only that file, so it kept listing a merged branch under "Needs you". The tree's own
#    research/fb_sim_backtest.json (main, once merged) decides. Asked through `status.build`, the
#    email itself, on a planted tree: the same fb-refit.json, without and with the entry recorded.
_t = tempfile.mkdtemp(prefix="injst-")
try:
    for _d in ("data/latest", "data/nfl/latest", "data/ncaaf/latest", "research"):
        os.makedirs(os.path.join(_t, _d))
    json.dump({"checked_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "findings": []},
              open(os.path.join(_t, "data", "latest", "health.json"), "w", encoding="utf-8"))
    json.dump({"injury_backtest": {"state": "measured", "branch": "fb/injuries-ncaaf-2026-10-19",
                                   "passes": True, "entry": dict(_PASS, questions=900)}},
              open(os.path.join(_t, "data", "ncaaf", "latest", "fb-refit.json"), "w", encoding="utf-8"))
    _rp = os.path.join(_t, "research", "fb_sim_backtest.json")
    json.dump({"injuries": {"nfl": {}}}, open(_rp, "w", encoding="utf-8"))
    _before = ST.build(root=_t, now=NOW)[1]
    json.dump({"injuries": {"nfl": {}, "ncaaf": dict(_PASS, questions=900)}}, open(_rp, "w", encoding="utf-8"))
    _after = ST.build(root=_t, now=NOW)[1]
finally:
    shutil.rmtree(_t, ignore_errors=True)
ck("🔴 [2026-10-26] the email lists the College branch while main has no ncaaf entry",
   any("College injuries" in n and "PASSED" in n for n in _before), str(_before)[:300])
ck("🔴 [2026-10-26] ...and stops the moment main holds it (the merge), though fb-refit.json still says "
   "measured", not any("College injuries" in n for n in _after), str(_after)[:300])
