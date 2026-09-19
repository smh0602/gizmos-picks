#!/usr/bin/env python3
"""§6's REFUSAL MUST SAY WHAT IS TRUE, AND MUST BE ABLE TO BE WRONG.

🔴🔴 WHAT WAS LIVE ON ALL 90 COLLEGE GAMES: *"Not enough college games
have been played yet... it needs about 80 teams' worth of well-timed
games... roughly the fourth week of the season, and this is the third."*

⛔ **THE CAUSE WAS WRONG.** `[measured 2026-09-18]` 336 games' worth of
plays were fetched and parsed — 10,132 drives, 299 teams, nothing
unparsed. The derivation REFUSED, over a play-ordering anomaly. The
coverage floor was never the binding constraint.

⛔ **AND IT WAS A CONSTANT.** The branch was `if _lg != "nfl": return
unavailable(...)` with no condition on any data, so it could never become
true or false. In week 10 it would still have said "this is the third".
➡️ A sentence that cannot be wrong cannot be right either — it is not a
measurement, it is a caption.

══════════════════════════════════════════════════════════════════════
✅ SO THIS FILE ASKS TWO QUESTIONS, AND THE SECOND IS THE ONE THAT BITES
══════════════════════════════════════════════════════════════════════
  1. **Does the text change with the data?** Three probe states, three
     different reader sentences. ⛔ A single string passing all three is
     the defect being re-shipped.
  2. **Does it refuse to name a cause it cannot know?** Two DIFFERENT
     refusals — a play-ordering anomaly and a coverage floor — must
     produce the SAME reader sentence and DIFFERENT `remedy`. 🔴 That is
     the check that stops the next author writing "the ordering is
     wrong" and shipping the original defect in a newer coat.

⚠️ `remedy` IS NOT READER-FACING and that is load-bearing here, not a
detail. `index.html` says so itself: *"`why` is the reader's sentence;
the remedy is the runbook's."* So the probe's own words, the filenames
and the percentages go there.

⚠️ No network, no credits. It builds throwaway trees.
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

import dossier_fb as D


# ══════════════════════════════════════════════════════════════════════
# @vacuity the refusal text must be DERIVED from the probe, not constant
#   file: dossier_fb.py
#   find:             if _probe is None:
#   with:             if True:
# ══════════════════════════════════════════════════════════════════════

SEASON = 2026
HOME, AWAY = "Alabama", "Auburn"


def _say(probe, league="ncaaf"):
    """§6 for one probe state. `probe=None` means the file is absent."""
    d = tempfile.mkdtemp(prefix="s6text-")
    try:
        latest = os.path.join(d, league, "latest")
        os.makedirs(latest)
        if probe is not None:
            json.dump(probe, io.open(
                os.path.join(latest, "top-probe-%d.json" % SEASON), "w",
                encoding="utf-8"))
        return D.s_possession(HOME, AWAY, SEASON,
                              data=os.path.join(d, league))
    finally:
        shutil.rmtree(d, ignore_errors=True)


_ABSENT = _say(None)
_ORDER = _say({"usable": False, "anomaly_pct": 36.282, "games": 336,
               "error": "36.28 pct of in-period play pairs ran backwards "
                        "or longer than 300s, over the 2.0 pct this trusts"})
_COVER = _say({"usable": False, "games": 336,
               "error": "only 41 team(s) clear the coverage floor, under "
                        "the 80 required"})
_USABLE = _say({"usable": True, "teams": 299})
_ALL = {"absent": _ABSENT, "ordering": _ORDER, "coverage": _COVER,
        "usable": _USABLE}

# ══════════════════════════════════════════════════════════════════════
section("1. ⚠️ EVERY STATE STILL REFUSES, AND SAYS SOMETHING (rule 67)")
# ══════════════════════════════════════════════════════════════════════
for _n, _r in sorted(_ALL.items()):
    ck("⚠️ %s: the section is UNAVAILABLE with a reason" % _n,
       _r.get("state") == "UNAVAILABLE" and len(_r.get("why") or "") > 60,
       "⛔ an empty or missing sentence would make every comparison below "
       "vacuous. state=%s why=%r"
       % (_r.get("state"), (_r.get("why") or "")[:60]))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 THE TEXT CHANGES WITH THE DATA — IT IS NOT A CONSTANT")
# ══════════════════════════════════════════════════════════════════════
_three = {_ABSENT["why"], _ORDER["why"], _USABLE["why"]}
ck("🔴🔴 three probe states produce THREE different reader sentences",
   len(_three) == 3,
   "⛔ THE WHOLE DEFECT. The old branch read no data at all and returned "
   "one hardcoded string for every state, so it could never become true "
   "or false. distinct=%d of 3" % len(_three))
ck("⛔ ...and none of them is the retired sentence",
   not any("fourth week" in r["why"] or "this is the third" in r["why"]
           or "80 teams" in r["why"] for r in _ALL.values()),
   "🔴 it named a cause that was not the cause — 336 games were parsed "
   "and the derivation refused over the play ordering, so the coverage "
   "floor was never the binding constraint")

# ⛔ AND THE SOURCE MUST REALLY READ THE PROBE, in CODE. Three different
#    strings could in principle come from three different constants; this
#    pins where they come from. Read from the parsed AST so a comment
#    naming the probe cannot satisfy it.
_fn = [n for n in ast.walk(ast.parse(io.open(
           os.path.join(ROOT, "dossier_fb.py"), encoding="utf-8").read()))
       if isinstance(n, ast.FunctionDef) and n.name == "s_possession"][0]
_reads = [ast.unparse(n) for n in ast.walk(_fn)
          if isinstance(n, ast.Call) and "top-probe" in ast.unparse(n)]
ck("🔴 `s_possession` reads the probe, in CODE",
   bool(_reads),
   "⛔ the sentence has to come FROM something. A branch that reads no "
   "data cannot be right or wrong, only repeated. calls found: %d"
   % len(_reads))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 ...BUT IT REFUSES TO NAME A CAUSE IT CANNOT KNOW")
# ══════════════════════════════════════════════════════════════════════
# 🔴 THE CHECK THAT STOPS THE DEFECT RETURNING IN A NEWER COAT. Today the
#    refusal is a play-ordering anomaly. Tomorrow it could be the coverage
#    floor. A reader sentence that asserts either one is the original
#    mistake with a fresher date on it.
ck("🔴🔴 two DIFFERENT refusals give the SAME reader sentence",
   _ORDER["why"] == _COVER["why"],
   "⛔ the reader sentence must describe THAT a check refused, never "
   "WHICH — we would be asserting a cause the sentence cannot verify. "
   "ordering=%r coverage=%r"
   % (_ORDER["why"][:60], _COVER["why"][:60]))
ck("✅ ...while the operator's `remedy` carries the probe's OWN words",
   _ORDER.get("remedy") != _COVER.get("remedy")
   and "play pairs" in _ORDER.get("remedy", "")
   and "coverage floor" in _COVER.get("remedy", ""),
   "⛔ the specific cause is not hidden, it is MOVED — `index.html`: "
   "'`why` is the reader's sentence; the remedy is the runbook's'. "
   "ordering=%r coverage=%r"
   % (_ORDER.get("remedy", "")[:70], _COVER.get("remedy", "")[:70]))
# ⛔ AND THE SAME SENTENCE MUST NOT NAME A CAUSE AT ALL. Two refusals
#    sharing a string is necessary but not sufficient: a string asserting
#    "the play ordering is wrong" would be shared by both AND wrong for
#    the coverage one, which is the original defect exactly.
_CAUSE_WORDS = ("ordering", "order", "coverage", "anomaly", "floor",
                "backwards", "clock was too", "too few games",
                "not enough games")
_named = [w for w in _CAUSE_WORDS if w in _ORDER["why"].lower()]
ck("🔴🔴 the refusal sentence names NO specific cause",
   not _named,
   "⛔ THE DEFECT IN A NEWER COAT. The sentence can say THAT a check "
   "refused; it cannot say WHICH, because the same sentence is served "
   "for every refusal and only one of them would be true. Move it to "
   "`remedy`. named: %s" % _named)

ck("✅ and the refusal reads as DELIBERATE, not as a breakage",
   "stand behind" in _ORDER["why"] and "doing its job" in _ORDER["why"],
   "⛔ a reader seeing a blank section assumes it is broken. A guard that "
   "declined to publish a number it could not stand behind is a FEATURE "
   "of this product and should read like one. why=%r"
   % _ORDER["why"][:90])

# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ THE READER'S SENTENCE IS FOR A READER")
# ══════════════════════════════════════════════════════════════════════
# Sam, 2026-08-26: "all of these things that a casual fine wont know
# about has to go." ⚠️ NOT a blanket no-digits rule — a season year is
# fine and every sentence here carries one.
for _n, _r in sorted(_ALL.items()):
    _w = _r["why"]
    ck("⛔ %s: no filename or path in the reader sentence" % _n,
       "/" not in _w and "\\" not in _w and ".json" not in _w
       and ".gz" not in _w,
       "🔴 the NFL branch was rewritten on 2026-09-17 for exactly this — "
       "it named a filename, a directory and a probe file, on all 32 "
       "games. why=%r" % _w[:90])
    ck("⛔ %s: no percentage and no bar in the reader sentence" % _n,
       "%" not in _w and "pct" not in _w.lower(),
       "🔴 `verify_card.py`'s jargon list is the standard. why=%r"
       % _w[:90])
    ck("⛔ %s: it claims no week and no date by which it will fill" % _n,
       "week" not in _w.lower() and "weekend" not in _w.lower(),
       "🔴 we do not know when it will fill — the ordering fix has not "
       "been acted on. why=%r" % _w[:90])

# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ THE NFL BRANCH IS NOT TOUCHED")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ It was already correct, and it is the voice the college branch was
#    rewritten INTO. Changing it here would be scope this task does not
#    own.
_NFL = _say(None, league="nfl")
ck("⛔ the NFL branch still says its own sentence",
   "either a build that has not run or a season whose clock is too "
   "patchy to use" in _NFL["why"],
   "🔴 rewritten 2026-09-17 and not this task's to change. why=%r"
   % _NFL["why"][:90])
ck("⚠️ ...and college's absent-probe case says the same thing",
   "either a build that has not run or a season whose clock is too "
   "patchy to use" in _ABSENT["why"],
   "✅ SAME SITUATION, SAME SENTENCE — when the probe is missing we know "
   "no more about college than about the NFL, and inventing a college-"
   "specific reason for it is how the old string got written")

note("absent/ordering/coverage/usable → %d distinct reader sentence(s), "
     "%d distinct remedies"
     % (len({r["why"] for r in _ALL.values()}),
        len({r.get("remedy") for r in _ALL.values()})))
