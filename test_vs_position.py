#!/usr/bin/env python3
"""§5 SHOWS SAM'S FOUR POSITIONS AND NOTHING ELSE.

`[Sam, 2026-09-18: "for player props i only want qb,rb,wr,te"]`

⛔ NOT A SORT, NOT THE BIGGEST GAPS, NOT THE WORST. The four carry the
props he bets. That is his call, already made, so the builder needs no
judgement and offers none — and this file's job is to keep it that way.

🔴 IT WAS ALREADY RIGHT BY ACCIDENT, AND THAT IS THE DEFECT.
`[measured 2026-09-18]` `allowed-by-position-2026.json.gz` holds exactly
QB, RB, TE, WR — 217 college defences, 32 NFL — so iterating the FILE's
keys produced the correct four today. ⛔ But `PROP_POS` in **both**
`cfb.py` and `nfl.py` is `{"QB", "RB", "WR", "TE", "FB"}` — five — so the
collectors are already scoped to gather a fullback, and the first FB row
would have put a fifth position on the page with nobody deciding.
⚠️ "It happens to agree" is the thing this project stops trusting; §6's
own comment says so in those words.

⛔ AND §5 STILL MOVES NOTHING. Its verdict stays: a one-standard-deviation
swing in defensive quality is worth about 4.4 rushing yards against
roughly 27 yards of held-out error. It must not feed a projection, a
confidence, a rank or a pick, and `audit()` must stay empty.

# @vacuity ⛔ exactly FOUR positions, and a fifth is not shown
#   file: dossier_fb.py
#   find: VS_POSITIONS = ("QB", "RB", "WR", "TE")
#   with: VS_POSITIONS = ("QB", "RB", "WR", "TE", "FB")
#
# @vacuity the page walks the DECLARED list, never the file's own keys
#   file: dossier_fb.py
#   find:         "positions": list(VS_POSITIONS),
#   with:         "positions": sorted(out.get(home) or out.get(away) or {}),
#
# @vacuity ⛔ the four are never ordered against each other
#   file: dossier_fb.py
#   find:         for pos in VS_POSITIONS:
#   with:         for pos in sorted(VS_POSITIONS, key=lambda p: -len(d.get(p) or {})):
#
# @vacuity a position with no numbers REFUSES BY NAME, never vanishes
#   file: dossier_fb.py
#   find:                 miss[pos] = no_position(t, pos)
#   with:                 pass
#
# @vacuity ...and the refusal claims nothing about the world
#   file: dossier_fb.py
#   find:         "why": ("We hold no numbers for %s against the %s%s."
#   with:         "why": ("%s has faced no %s%s."
#
# @vacuity §5 keeps the verdict that says it moves nothing
#   file: dossier_fb.py
#   find:          "verdict": VS_VERDICT,
#   with:          "verdict": "",
#
# @vacuity a position the file holds beyond the four is NAMED, not dropped silently
#   file: dossier_fb.py
#   find:         dropped |= {p for p in d if p not in VS_POSITIONS}
#   with:         dropped |= set()
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

import dossier_fb as D          # noqa: E402
import jsblock                  # noqa: E402

DSRC = io.open(os.path.join(ROOT, "dossier_fb.py"), encoding="utf-8").read()
HTML = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()


def allowed_file(defences, season=2026):
    return {season: {"season": season,
                     "rank_note": "rank 1 = ALLOWS THE MOST",
                     "defences": defences}}


FULL = {"games": 3, "rec_yds_rank": 12, "rush_yds_rank": 40}


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 EXACTLY FOUR, AND THEY ARE SAM'S FOUR")
# ══════════════════════════════════════════════════════════════════════
ck("the four are a fixed declared list, not derived",
   isinstance(D.VS_POSITIONS, tuple), "VS_POSITIONS=%r" % (D.VS_POSITIONS,))
ck("🔴 EXACTLY four", len(D.VS_POSITIONS) == 4,
   "⛔ his words were four. VS_POSITIONS=%s" % (D.VS_POSITIONS,))
ck("🔴 ...and they are QB, RB, WR, TE",
   set(D.VS_POSITIONS) == {"QB", "RB", "WR", "TE"},
   "VS_POSITIONS=%s" % (D.VS_POSITIONS,))
ck("...in the order he typed them, which is not a ranking",
   list(D.VS_POSITIONS) == ["QB", "RB", "WR", "TE"],
   "\"qb,rb,wr,te\" — the order carries no meaning and the artifact says so")

# ⛔ THE SECTION ITERATES THE DECLARED LIST, NOT THE FILE'S KEYS. This is
#    the whole change: the old form read `sorted(d)`.
_fn = DSRC[DSRC.index("def s_vs_position("):]
_fn = _fn[:_fn.index("\ndef ")]
ck("🔴 the builder walks VS_POSITIONS",
   "for pos in VS_POSITIONS:" in _fn,
   "⛔ iterating the file's own keys is what made this right by accident")
ck("⛔ ...and no longer walks the file's keys",
   "for pos in sorted(d)" not in _fn and "sorted(d)}" not in _fn,
   "found a data-driven iteration")


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 A FIFTH POSITION IN THE FILE IS NOT SHOWN, AND IS NAMED")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ DRIVEN AGAINST A FULLBACK ROW, because `PROP_POS` already includes
#    FB in both collectors — this is the case that arrives on its own.
five = allowed_file({
    "Alabama": {p: dict(FULL) for p in ("QB", "RB", "WR", "TE", "FB")},
    "Georgia": {p: dict(FULL) for p in ("QB", "RB", "WR", "TE")}})
s5 = D.s_vs_position("Alabama", "Georgia", five, 2026)
ck("the section still reads OK with a fifth position in the file",
   s5.get("state") == "OK", "state=%r" % (s5.get("state"),))
ck("🔴 FB is NOT in what the page is given",
   "FB" not in (s5.get("positions") or [])
   and all("FB" not in v for v in (s5.get("by_defence") or {}).values()),
   "⛔ positions=%s alabama=%s"
   % (s5.get("positions"),
      sorted((s5.get("by_defence") or {}).get("Alabama") or {})))
ck("🔴 ...and it is NAMED as not shown, not dropped in silence",
   s5.get("positions_not_shown") == ["FB"]
   and "FB" in (s5.get("positions_not_shown_note") or ""),
   "⛔ silently discarding a position is the same class of quiet as "
   "silently showing one. note=%r" % (s5.get("positions_not_shown_note"),))
ck("the declared list travels with the data",
   s5.get("positions") == ["QB", "RB", "WR", "TE"],
   "positions=%s" % (s5.get("positions"),))
ck("...and it says the four are not ordered against each other",
   "not ordered against each other" in (s5.get("positions_note") or ""),
   "positions_note=%r" % (s5.get("positions_note"),))


# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 A POSITION WITH NO NUMBERS REFUSES BY NAME")
# ══════════════════════════════════════════════════════════════════════
# ⛔ NOT A ZERO, NOT A BLANK, NOT AN OMISSION. College §5 already reads
#    unavailable on 16 games where the opponent is unresolved; a missing
#    position is the same shape one level down.
norb = allowed_file({
    "Alabama": {p: dict(FULL) for p in ("QB", "RB", "WR", "TE")},
    "Georgia": {p: dict(FULL) for p in ("QB", "WR", "TE")}})   # no RB
s3 = D.s_vs_position("Alabama", "Georgia", norb, 2026)
ck("the other three still show for that team",
   sorted((s3.get("by_defence") or {}).get("Georgia") or {})
   == ["QB", "TE", "WR"],
   "georgia=%s" % (sorted((s3.get("by_defence") or {}).get("Georgia") or {}),))
ck("🔴 RB REFUSES, and it is named",
   (s3.get("not_held") or {}).get("Georgia", {}).get("RB", {}).get("state")
   == "UNAVAILABLE",
   "not_held=%s" % (s3.get("not_held"),))
# ⛔ `.get`-CHAINED, NOT SUBSCRIPTED. With the refusal mutated away
#    these keys are absent, and a bare subscript makes the file DIE
#    instead of FAIL — a red run with no named check, which this repo
#    has shipped before. A guard must fail, not crash.
_rb = ((s3.get("not_held") or {}).get("Georgia") or {}).get("RB") or {}
_why = _rb.get("why") or ""
ck("...and the refusal names the team AND the position in words",
   "Georgia" in _why and "running back" in _why,
   "why=%r" % (_why,))
ck("🔴 ...and it claims something about OUR RECORDS, not about the team",
   _why.lower().startswith("we hold no"),
   "⛔ \"Georgia has faced no running backs\" is a sentence about football "
   "this file cannot support. Corrected twice already in this repo. "
   "why=%r" % (_why,))
ck("...and it says what would change it",
   bool(_rb.get("remedy")),
   "a gap that does not say what would fill it is a shrug")
ck("⛔ RB is NOT present as a zero or an empty row",
   "RB" not in ((s3.get("by_defence") or {}).get("Georgia") or {}),
   "an empty dict beside three real ones reads as 'ranked zero'")

# 🔴 A DEFENCE WE HOLD NOTHING FOR REFUSES ON ALL FOUR.
none_at_all = allowed_file({
    "Alabama": {p: dict(FULL) for p in ("QB", "RB", "WR", "TE")}})
s3b = D.s_vs_position("Alabama", "Nowhere State", none_at_all, 2026)
ck("a team absent from the file refuses on all four, by name",
   sorted((s3b.get("not_held") or {}).get("Nowhere State", {}))
   == ["QB", "RB", "TE", "WR"],
   "⛔ the old form dropped the team entirely, which is how 19 college "
   "rows read OK with one defence in them. not_held=%s"
   % ({k: sorted(v) for k, v in (s3b.get("not_held") or {}).items()},))
ck("...and says we hold nothing for that defence at all",
   "at all" in (((s3b.get("not_held") or {}).get("Nowhere State") or {})
                 .get("QB") or {}).get("why", ""),
   "not_held=%s" % (s3b.get("not_held"),))

# ⛔ NEITHER SIDE HELD -> THE WHOLE SECTION REFUSES, not a half answer.
s3c = D.s_vs_position("A", "B", none_at_all, 2026)
ck("🔴 with neither defence held, the SECTION refuses",
   s3c.get("state") == "UNAVAILABLE",
   "state=%r why=%r" % (s3c.get("state"), (s3c.get("why") or "")[:80]))
ck("...and says what would fill it", bool(s3c.get("remedy")),
   "remedy=%r" % (s3c.get("remedy"),))


# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ §5 STILL MOVES NOTHING")
# ══════════════════════════════════════════════════════════════════════
ck("the verdict that says so is still attached",
   s5.get("verdict") == D.VS_VERDICT and bool(D.VS_VERDICT),
   "⛔ a rank shown without that sentence reads as a reason to bet")
ck("...and it still carries both measured numbers",
   "4.4" in D.VS_VERDICT and "27" in D.VS_VERDICT,
   "the ranking is real and far smaller than the noise it sits inside. "
   "verdict=%r" % (D.VS_VERDICT[:90],))
ck("...and it still says DISPLAYED, NOT APPLIED",
   "DISPLAYED, NOT APPLIED" in D.VS_VERDICT, "verdict changed")
ck("the section is DESCRIPTIVE, never MODEL",
   s5.get("basis") == D.DESC, "basis=%r" % (s5.get("basis"),))
for _f in ("confidence", "projection", "pick", "score", "edge", "blend"):
    ck("⛔ §5 emits no %r field" % _f,
       not any(_f in str(k).lower() for k in s5),
       "keys=%s" % (sorted(s5),))
_found, _missing = D.audit(s5)
ck("🔴 audit() finds NO judgement-shaped number anywhere in §5",
   not _found, "⛔ empty is the only acceptable answer. found=%s" % (_found,))
_found3, _ = D.audit(s3)
ck("...including on a section carrying a refusal",
   not _found3, "found=%s" % (_found3,))


# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE PAGE SHOWS THE FOUR, AND ONLY THE FOUR")
# ══════════════════════════════════════════════════════════════════════
_js = jsblock.js_block("fbDosFacts", os.path.join(ROOT, "index.html"))
ck("the panel walks the declared list",
   "s.positions" in _js,
   "⛔ it must not iterate by_defence's own keys")
ck("⛔ ...and no longer walks the data's keys for §5",
   "Object.keys(d).forEach(pos" not in _js,
   "found the old data-driven iteration")
ck("a refusal is printed VERBATIM from the builder (rule 132)",
   "r.why}" in _js.replace(" ", "") or "${r.why}" in _js,
   "the page places the sentence; it does not write one")
ck("the not-shown note is printed too",
   "positions_not_shown_note" in _js,
   "a dropped position is named on the page, not only in the file")


def render(sec):
    out = subprocess.run(
        ["node", "-e", """
const fs=require('fs');const h=fs.readFileSync('index.html','utf8');
const m=h.match(/function fbDosFacts\\(s\\)\\{[\\s\\S]*?\\n\\}/);
eval(m[0].replace('function fbDosFacts','var fbDosFacts = function'));
console.log(fbDosFacts(JSON.parse(process.argv[1])));
""", __import__("json").dumps(sec)],
        capture_output=True, text=True, cwd=ROOT)
    return out.stdout


# ⚠️ DRIVEN IN A REAL JS ENGINE AGAINST THE REAL FILE, not against my
#    reading of it (rule 197: found by loading the page, not reading it).
_h = render(s5)
ck("the rendered panel names all four positions",
   all(("vs %s" % p) in _h for p in ("QB", "RB", "WR", "TE")),
   "html=%r" % (_h[:300],))
ck("🔴 ...and the fifth NEVER reaches the page",
   "vs FB" not in _h,
   "⛔ html=%r" % (_h[:400],))
ck("...while the page still SAYS the file holds it",
   "also holds FB" in _h, "html=%r" % (_h[:400],))

_h3 = render(s3)
ck("🔴 a missing position renders its refusal, in its own place",
   "We hold no numbers for Georgia against the running back" in _h3,
   "html=%r" % (_h3[:400],))
ck("⛔ ...and does not render as a zero or an empty row",
   "Georgia vs RB" not in _h3, "html=%r" % (_h3[:400],))
ck("...and the other three still render for that team",
   all(("Georgia vs %s" % p) in _h3 for p in ("QB", "WR", "TE")),
   "html=%r" % (_h3[:400],))

# 🔴 THE HARD CASE: a section whose DATA holds a fifth but whose declared
#    list does not. The page must follow the declaration.
_rogue = dict(s5)
_rogue["by_defence"] = {"Alabama": {p: {"games": 3} for p in
                                    ("QB", "RB", "WR", "TE", "FB")}}
_hr = render(_rogue)
ck("🔴 a fifth position sitting in by_defence is still not rendered",
   "vs FB" not in _hr,
   "⛔ the page follows the DECLARED list, so bad data cannot show a "
   "position nobody chose. html=%r" % (_hr[:300],))


# ══════════════════════════════════════════════════════════════════════
section("6. ⛔ NO JARGON IN THE NEW PROSE")
# ══════════════════════════════════════════════════════════════════════
# Sam, 2026-08-26: "lose the technical wording ... all of these things
# that a casual fine wont know about has to go." `verify_card.py` fails
# the MLB build on a jargon list; the same standard governs here.
_prose = " ".join([
    _rb.get("why") or "",
    _rb.get("remedy") or "",
    s5.get("positions_note") or "",
    s5.get("positions_not_shown_note") or "",
    s3c.get("why") or "", s3c.get("remedy") or "",
])
for _bad in ("percentile", "z-score", " sd ", "std", "VS_POSITIONS",
             "PROP_POS", "allowed-by-position", "dict", "None"):
    ck("⛔ %r is absent from the new prose" % _bad,
       _bad.lower() not in _prose.lower(), "prose=%r" % (_prose[:200],))
ck("⚠️ and the position is spelled out for a reader, not left as a code",
   "running back" in _prose and "RB." not in _prose,
   "a casual reader knows 'running back'. prose=%r" % (_prose[:160],))


# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 THE REAL BOARDS — EVERY TEAM ACCOUNTS FOR ALL FOUR")
# ══════════════════════════════════════════════════════════════════════
# ⛔ DRIVEN AGAINST THE LIVE ARTIFACTS, NOT AGAINST MY READING OF THEM.
#    CLAUDE.md: a guard that fires on correct code is the other failure,
#    and the only way to know is to run it on the real thing.
# 🔴 THE INVARIANT: for every defence in an OK §5, SHOWN + REFUSED must
#    cover the four exactly. A position that is neither shown nor refused
#    has vanished, which is the defect this task closes.
# ⚠️ MEASURED 2026-09-18 on the stored boards: 4 college defences hold
#    QB/RB/WR and NO TE, and Northwestern is absent from the file
#    entirely — 9 refusals that previously produced no output at all.
import gzip                                              # noqa: E402
import json                                              # noqa: E402

_ran = 0
for _lg in ("ncaaf", "nfl"):
    _root = os.path.join(ROOT, "data", _lg)
    try:
        _board = json.load(io.open(os.path.join(_root, "latest",
                                                "board.json"),
                                   encoding="utf-8"))
    except Exception as e:
        note("%s: no stored board (%s) — skipped" % (_lg, e))
        continue
    _games = _board.get("games") or []
    # ⛔ AN EMPTY BOARD MUST NOT LOOK LIKE A PASS (rule 67).
    ck("⚠️ %s has a real board to drive against" % _lg,
       len(_games) > 5, "%d game(s)" % len(_games))
    if len(_games) <= 5:
        continue
    _resolve = D.team_codes(_lg)
    _allowed = {}
    for _yr in (2026, 2025):
        try:
            _allowed[_yr] = json.load(gzip.open(os.path.join(
                _root, "latest", "allowed-by-position-%d.json.gz" % _yr),
                "rt"))
        except Exception:
            pass
    _bad, _fifth, _ok, _refused = [], [], 0, 0
    for _g in _games:
        _h, _a = _resolve(_g.get("home")), _resolve(_g.get("away"))
        _miss = None
        if not (_h and _a):
            _miss = [n for n, r in ((_g.get("home"), _h),
                                    (_g.get("away"), _a)) if not r]
        _s = D.s_vs_position(_h, _a, _allowed, 2026, _miss)
        if _s.get("state") != "OK":
            continue
        _ok += 1
        _held = _s.get("by_defence") or {}
        _gone = _s.get("not_held") or {}
        for _t in set(_held) | set(_gone):
            _cover = set(_held.get(_t) or {}) | set(_gone.get(_t) or {})
            if _cover != set(D.VS_POSITIONS):
                _bad.append((_t, sorted(_cover)))
            _refused += len(_gone.get(_t) or {})
        _fifth += [p for p in (_s.get("positions") or [])
                   if p not in D.VS_POSITIONS]
    note("%s: %d OK section(s), %d position refusal(s) by name"
         % (_lg, _ok, _refused))
    ck("🔴 %s: every defence accounts for ALL FOUR — shown or refused "
       "by name" % _lg,
       not _bad,
       "⛔ a position that is neither shown nor refused has VANISHED, "
       "which is what this task closes. offenders: %s" % (_bad[:6],))
    ck("⛔ %s: no position outside the four is offered to the page" % _lg,
       not _fifth, "found: %s" % (_fifth,))
    _ran += 1

ck("🔴🔴 ...and this section actually ran on a real board",
   _ran >= 1,
   "⛔ if neither board is on disk this file proves nothing about "
   "production (rule 67). leagues driven: %d" % _ran)
