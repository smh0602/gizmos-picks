#!/usr/bin/env python3
"""
🔴 THE VERSION STAMP AND THE COEFFICIENTS MUST MOVE TOGETHER.

`claude/mlb-projection-model.md` published **v5.0 on 2026-09-01**. The
card kept running **v4.0** until **2026-09-11** — ten days — and its
stamp said `v4.0` the whole time, **correctly**. Nothing was lying; the
two halves of the re-fit had simply come apart, and the only thing that
noticed was a scheduled grading run re-reporting it into a list nobody
was reading (rule 171, again).

⛔ **A RE-FIT THAT UPDATES THE DOC AND STOPS HAS SHIPPED NOTHING.**
`claude/owed-tests.md` step 14 says exactly that: *"the card is the
surface Sam reads, and `card.py` hard-codes v4.0."*

✅ **WHAT THIS FILE PINS, AND WHAT IT DELIBERATELY DOES NOT.**

It does **NOT** assert the coefficients' VALUES. `mlb-projection-model.md`
OWNS those, and a copy of them here would be a second source of truth —
the exact pattern this project bans, and the one that put v4.0's numbers
into `card-blueprint.md` where a card builder read them first.

⛔ What it asserts instead is that the STAMP AND THE CONSTANTS CANNOT
DRIFT APART SILENTLY: the model block carries a FINGERPRINT recorded
beside its version, so changing a coefficient without bumping the version
— or bumping the version without changing a coefficient — fails here.

➡️ **ON THE NEXT RE-FIT:** update the constants, bump `MODEL_VERSION`,
run this file, and paste the fingerprint it prints into `MODEL_FINGERPRINT`.
That is three deliberate acts instead of one silent one.
"""
import hashlib
import os
import sys

from tcheck import ck, eq, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import card  # noqa: E402

# ⛔ THE CONSTANTS THE MODEL DOC OWNS. Named here, never valued here.
NAMES = ("K_INTERCEPT", "K_TRAIL_B", "K_TRAIL_C", "K_OPP_B", "K_HOME",
         "O_INTERCEPT", "O_TRAIL_C", "O_NP_B", "O_NP_C", "O_HOME",
         "O_TIER_CUT_LO", "O_TIER_CUT_HI",
         "O_TIER_B_LO", "O_TIER_B_MID", "O_TIER_B_HI", "TRAIL_N")

print("\n═══ 1. 🔴 EVERY MODEL CONSTANT IS STILL WHERE ONE EDIT REACHES IT ═══")
missing = [n for n in NAMES if not hasattr(card, n)]
ck("🔴 all 16 model constants are module-level in card.py",
   not missing,
   "⛔ a coefficient buried as a literal inside a function is one this "
   "check cannot see and a re-fit will miss: %s" % (missing or "none"))
ck("...and the CODE-DEBT table's count still holds",
   len(NAMES) == 16,
   "16 is the number `mlb-projection-model.md` compared against; if this "
   "changes, that table needs a row")


def fingerprint():
    blob = ";".join(f"{n}={getattr(card, n)!r}" for n in NAMES)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


print("\n═══ 2. 🔴 THE STAMP AND THE COEFFICIENTS MOVE TOGETHER ═══")
# 🔴 Bump BOTH on a re-fit. This is the guard that would have caught
#    v5.0-in-the-doc / v4.0-in-the-card on day one instead of day ten.
MODEL_VERSION = "v5.0"
MODEL_FINGERPRINT = "a7c97709dc04dce5"   # v5.0, re-fit 2026-09-01, shipped 2026-09-11

fp = fingerprint()
ck("the card states which model version it ships",
   getattr(card, "MODEL_VERSION", None) == MODEL_VERSION,
   "card says %r, this file expects %r — if a re-fit shipped, bump BOTH "
   "and re-run" % (getattr(card, "MODEL_VERSION", None), MODEL_VERSION))
ck("🔴 ...and the coefficients match that version's fingerprint",
   fp == MODEL_FINGERPRINT,
   "constants fingerprint %s, expected %s. ⛔ IF A COEFFICIENT CHANGED, "
   "BUMP `MODEL_VERSION` IN card.py AND PASTE THIS FINGERPRINT HERE — "
   "a coefficient that moves without the stamp moving is how the card "
   "ran v4.0 for ten days after the doc shipped v5.0" % (fp, MODEL_FINGERPRINT))

print("\n═══ 3. \U0001f534 AND NO OTHER FILE RESTATES ONE ═══")
# \U0001f534 THE FINGERPRINT ABOVE GUARDS card.py AND CANNOT SEE A COPY
#    SOMEWHERE ELSE — AND THERE WAS ONE. `[2026-09-11]` `verify_card.py`
#    hard-coded v4.0's EIGHT outs coefficients to recompute the Normal
#    probability. v5.0 shipped to `card.py` at 01:11Z; from 11:13Z every
#    MLB converge pass wrote `card-verify-failure.txt`, **blocked the
#    card and turned the run red, hourly — on a CORRECT card.**
#    ```
#    verify_card.py's literals (v4.0)   max gap 1.8258 pts   FAIL
#    card.py's own constants (v5.0)     max gap 0.0424 pts   PASS
#    ```
# ⛔ RULE 66, AND THE THIRD PLACE IT HAS BITTEN: `card-blueprint.md` held
#    v4.0's coefficients where a builder read them first; `index.html`
#    ranked a second time in JavaScript; and the VERIFIER kept its own
#    model. ➡️ **A SECOND COPY OF A COEFFICIENT IS A SECOND THING TO
#    DRIFT, AND IT DRIFTS SILENTLY UNTIL A BOARD HAPPENS TO PRICE THE ROW
#    THAT EXPOSES IT.**
# ✅ SO THE SEARCH IS DERIVED FROM card.py's OWN VALUES rather than from a
#    list anyone maintains: whatever the constants are today, no other
#    source file may contain their literal text.
_VALUES = {n: getattr(card, n) for n in NAMES}
# ⚠️ Only values distinctive enough that a match is evidence. `TRAIL_N=8`
#    and a cut-point like `17.0` occur all over ordinary code, so a hit on
#    them says nothing; a 4-significant-figure coefficient is a signature.
_DISTINCT = {n: v for n, v in _VALUES.items()
             if isinstance(v, float) and len(repr(v).split(".")[-1]) >= 3}
_SKIP = {"card.py", "test_model_version.py"}
_hits = []
for _f in sorted(os.listdir(ROOT)):
    if not _f.endswith(".py") or _f in _SKIP:
        continue
    try:
        _src = open(_f, encoding="utf-8").read()
    except Exception:
        continue
    # ⛔ COMMENTS AND STRUCK LINES DO NOT COUNT. A struck coefficient kept
    #    visibly beside its replacement is this project's own convention
    #    (Sam's standing rule), and reading it as a live copy would punish
    #    exactly the thing we want people to keep doing.
    _live = "\n".join(l for l in _src.splitlines()
                       if not l.lstrip().startswith("#"))
    for _n, _v in _DISTINCT.items():
        if repr(_v) in _live:
            _hits.append("%s carries %s=%r" % (_f, _n, _v))
ck("\U0001f534 no file but card.py contains a model coefficient's literal value",
   not _hits,
   "⛔ %s. A recomputation is allowed — REQUIRED, even — to rebuild mu a "
   "second and different way from the raw log. What it may not do is "
   "restate the COEFFICIENTS: those are the model's specification, owned "
   "by `claude/mlb-projection-model.md`, and a copy of them is a second "
   "source of truth. ➡️ Import them from card.py instead."
   % ("; ".join(_hits) if _hits else "none"))
ck("✅ ...and this search is DERIVED, so it re-aims itself at the next re-fit",
   len(_DISTINCT) >= 10,
   "⛔ the needles come from card.py's CURRENT values — a hard-coded list "
   "of old coefficients would go stale the same way the copy did. "
   "%d distinctive constant(s) searched for" % len(_DISTINCT))
ck("⚠️ ...and verify_card.py really does still rebuild mu itself",
   all(t in open("verify_card.py", encoding="utf-8").read()
       for t in ("mu =", "math.erf", "tr[-1]['np']")),
   "\u26d4 THE FIX MUST NOT BECOME `mu = card.outs_mu(...)`. That would "
   "make the verifier reuse the arithmetic it exists to check "
   "independently, which is what its own docstring forbids. Importing a "
   "CONSTANT is not importing a CALCULATION")


print("\n═══ 4. \U0001f534 AND NO SHIPPED STRING NAMES A VERSION IN PROSE ═══")
# \U0001f534 THE FINGERPRINT PROVED THE CONSTANTS AND THE STAMP MOVED
#    TOGETHER, AND THE CARD STILL TOLD THE READER "v4.0". `[2026-09-11]`
#    Three strings named v4.0 while `MODEL_VERSION` correctly said v5.0,
#    and TWO OF THEM REACH THE PAGE:
#      confidence_note   "v4.0 model blended 50/50 with his own rate..."
#      joint_note        "Every leg is a v4.0 model estimate."
#      the module docstring
# ⛔ THAT IS A FALSE PROVENANCE CLAIM ON A PAGE REAL MONEY IS BET
#    AGAINST — the same class as rule 184, where a stamp and the code
#    disagreed, except here the STAMP was right and the PROSE was lying.
# ➡️ A VERSION IS A FACT ABOUT THE CODE. READ IT, NEVER RETYPE IT.
# ✅ DOCSTRINGS AND COMMENTS ARE EXEMPT ON PURPOSE: they are where the
#    project records what a number USED to be, and Sam's standing rule is
#    that superseded content stays visible rather than being deleted.
#    Only literals that can reach `picks/<date>.json` or the page count,
#    so this walks the AST rather than grepping lines.
import ast  # noqa: E402
import re  # noqa: E402

_src = open("card.py", encoding="utf-8").read()
_tree = ast.parse(_src)
_docs = set()
for _n in ast.walk(_tree):
    _b = getattr(_n, "body", None)
    if isinstance(_n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                       ast.ClassDef)) and _b \
            and isinstance(_b[0], ast.Expr) \
            and isinstance(_b[0].value, ast.Constant) \
            and isinstance(_b[0].value.value, str):
        _docs.add(id(_b[0].value))
_lits = [(_n.lineno, _n.value) for _n in ast.walk(_tree)
         if isinstance(_n, ast.Constant) and isinstance(_n.value, str)
         and id(_n) not in _docs
         and re.search(r"\bv\d+\.\d+\b", _n.value)]
# ⚠️ THE DEFINITION ITSELF IS THE ONE ALLOWED LITERAL. Everything else
#    must interpolate it.
_bad = [(ln, v[:70]) for ln, v in _lits if v.strip() != MODEL_VERSION]
ck("\U0001f534 no shipped string in card.py names a model version in prose",
   not _bad,
   "⛔ %s. These reach the card file and the page. ➡️ Interpolate "
   "`MODEL_VERSION` instead: the card ran v5.0 from 01:11Z on 2026-09-11 "
   "while three strings still said v4.0" % (_bad or "none"))
eq(len(_lits), 1,
   "✅ exactly one literal version in the whole file — the definition")
ck("✅ ...and the reader-facing strings really do interpolate it",
   ("MODEL_VERSION + \" model blended" in _src
    or "MODEL_VERSION" in _src.split("confidence_note")[1][:200])
   and "% MODEL_VERSION" in _src,
   "⛔ `confidence_note` and the MODEL parlay label are the two a reader "
   "sees; a fix that only touched the docstring would leave the page "
   "lying and this check passing")
ck("⚠️ ...and the struck originals are kept, not deleted",
   "~~\"v4.0 model blended" in _src or '~~"v4.0 model blended' in _src,
   "Sam's standing rule: superseded content stays visible with a reason, "
   "so the next reader knows what it used to claim and why it changed")


note("⚠️ THIS FILE DOES NOT OWN THE VALUES. "
     "`claude/mlb-projection-model.md` does, and copying them here would "
     "be the second-source-of-truth pattern that put v4.0's numbers into "
     "card-blueprint.md where a card builder read them first. ⛔ What is "
     "owned here is only that the two halves of a re-fit ship together.")
note("current fingerprint: " + fp)
