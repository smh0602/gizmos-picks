#!/usr/bin/env python3
"""
🔴🔴 `index.html` IS SHARED WITH MLB, AND MLB IS FROZEN.

Sam, 2026-09-12: *"we have mlb perfected we dont need to touch it."*
`CLAUDE.md` puts `card.py`, `verify_card.py` and the MLB card off limits
— but the page is ONE FILE and every football feature is written into it
beside the MLB half. ⛔ **"I did not change the MLB call site" is not
proof that MLB renders the same.** This file is that proof.

✅ IT IS THE `research/bandrow_pre_saidas.js` LICENCE, WIDENED. That
oracle froze ONE shared component so a football change to it could be
shown to render MLB's real calibration byte-identically. This freezes
**every top-level function whose name does not start `fb`, and every CSS
rule**, as digests taken from `origin/main` at 407afad.

⚠️ THAT IS MORE THAN THE MLB TABS, DELIBERATELY. `sgn`, `bandRow`,
`betLink`, `boardFor`, `freshness` and `priceCell` are SHARED helpers.
Teaching one of them about football is editing MLB through the back door,
and the freeze forbids that as surely as editing the card.

⛔ WHAT IS ALLOWED: adding a function whose name starts `fb`, and adding
a CSS selector nothing frozen uses. ⛔ WHAT IS NOT: changing or removing
a frozen function or rule, or adding a selector that collides with one —
an "addition" that overrides `.note` changes the MLB render as surely as
editing it.

⛔ AND DO NOT REGENERATE THE ORACLE TO MAKE A RUN GREEN. The moment it
tracks the live page it proves nothing. This file fails if the oracle is
empty or if it has grown to cover football, both of which are what a
lazy regeneration looks like.
"""

# ══════════════════════════════════════════════════════════════════════
# @vacuity an MLB-side render cannot be changed without this going red
#   file: index.html
#   find: async function jget(u){ const r = await fetch(u); if(!r.ok) throw new Error(u+' -> '+r.status); return r.json(); }
#   with: async function jget(u){ const r = await fetch(u); if(!r.ok) throw new Error(u+' :: '+r.status); return r.json(); }
#
# @vacuity ...and neither can an MLB-side CSS rule
#   file: index.html
#   find: .msg{padding:40px 0;text-align:center;color:var(--mut)}
#   with: .msg{padding:41px 0;text-align:center;color:var(--mut)}
# ══════════════════════════════════════════════════════════════════════

import hashlib
import json
import os

from jsblock import css_rules, top_level_blocks
from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, "index.html")
ORACLE = os.path.join(ROOT, "research", "mlb_render_frozen.json")


def h(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:24]


section("1. ⚠️ THE ORACLE IS REAL, AND IT IS NOT THE LIVE PAGE")
F = json.load(open(ORACLE, encoding="utf-8"))
_fz, _cz = F.get("functions") or {}, F.get("css") or {}
ck(len(_fz) >= 30 and len(_cz) >= 200,
   "⛔ it covers the page (%d function(s), %d rule(s))" % (len(_fz), len(_cz)),
   "🔴 rule 67: an empty or thin oracle passes forever having compared "
   "nothing, and that is exactly what a lazy regeneration produces")
_fb = sorted(k for k in _fz if k.startswith("fb"))
ck(not _fb,
   "⛔ ...and it has NOT grown to cover football",
   "🔴 THE FREEZE IS ON MLB, NOT ON FOOTBALL. An oracle that pins `fb*` "
   "would redden on every legitimate football change and get "
   "regenerated on sight — which is how an oracle stops being one "
   "(rule 238). Found %s" % _fb)

section("2. 🔴🔴 NOT ONE MLB-SIDE FUNCTION HAS MOVED")
_now = top_level_blocks(PAGE)
_gone = sorted(k for k in _fz if k not in _now)
ck(not _gone,
   "   every frozen function is still on the page",
   "⛔ a shared helper DELETED is an MLB tab that stops drawing. "
   "Missing: %s" % _gone)
_moved = sorted(k for k in _fz if k in _now and h(_now[k]) != _fz[k])
ck(not _moved,
   "🔴🔴 ...AND EVERY ONE IS BYTE-IDENTICAL (%d checked)" % len(_fz),
   "⛔ THE MLB FREEZE. If one of these had to change, that is Sam's "
   "decision and not a fixture edit — `CLAUDE.md`: \"it was broken so I "
   "touched it\" is precisely the reasoning the rule exists to refuse. "
   "Changed: %s" % _moved)

section("3. ⛔ NOR ONE CSS RULE MLB DRAWS INTO")
_cnow = css_rules(PAGE)
_cgone = sorted(k for k in _cz if k not in _cnow)
ck(not _cgone,
   "   every frozen rule is still there",
   "⛔ a removed rule is an unstyled MLB table. Missing: %s" % _cgone[:6])
_cmoved = sorted(k for k in _cz if k in _cnow and h(_cnow[k]) != _cz[k])
ck(not _cmoved,
   "🔴 ...and none of their declarations changed (%d checked)" % len(_cz),
   "⛔ a render is the functions AND the rules they draw into. "
   "Changed: %s" % _cmoved[:6])
_added = sorted(k for k in _cnow if k not in _cz)
ck(not (set(_added) & set(_cz)),
   "✅ ...while %d ADDED selector(s) are allowed and collide with none"
   % len(_added),
   "🔴 AN ADDITION THAT OVERRIDES A FROZEN SELECTOR CHANGES THE MLB "
   "RENDER AS SURELY AS EDITING IT. Colliding: %s"
   % sorted(set(_added) & set(_cz)))
note("   added selector(s): %s" % (_added or "none"))
note("   football functions on the page: %d, and none of them is frozen "
     "— the freeze is on MLB, not on football."
     % len([k for k in _now if k.startswith("fb")]))
note("⛔ WHAT THIS FILE DOES NOT CLAIM: that the MLB tabs are correct, or "
     "that they render at all. It claims they render EXACTLY AS THEY DID "
     "at 407afad — which is the only thing a football change is allowed "
     "to promise about them.")
