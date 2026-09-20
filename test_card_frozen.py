#!/usr/bin/env python3
"""
A PUBLISHED CARD IS FROZEN THE MOMENT ITS SLATE STARTS — IN EVERY LEAGUE.

🔴🔴 CLAUDE.md has carried this rule since MLB shipped: *"`picks/<date>.json`
already written — published estimates are a permanent record. ⛔ Never edit
or delete one after its games have started."* **Football never enforced it,
and nothing in the repo ever asked.**

`[measured 2026-09-19 across every dated card in `picks/`]`

    MLB        0 of 28 rewritten after their own first kickoff
    NFL        4 of  5
    NCAAF      7 of  8      — 11 of 13 football cards, 85%

⛔ AND THE DAMAGE IS NOT "SOME PRICES MOVED".
`picks/fb-nfl-2026-09-17.json` — whose first kickoff was 00:15Z on the
18th — was rewritten at 15:52Z on the 18th and now carries **the
2026-09-20 game lines**. The permanent record of what this product
advertised on the 17th is partly a different week's board. Two others are
39 hours late and one is 112.

══════════════════════════════════════════════════════════════════════
THE THREE HALVES, AND THE THIRD IS THE ONE THAT CANNOT BE FAKED
══════════════════════════════════════════════════════════════════════
  §1 `publish_dated()` is DRIVEN against real bytes on disk — written
     when the slate is ahead, refused when it has started, and the file
     compared byte for byte either way.
  §2 the decision function on every branch, including the two ways it
     can fail to tell.
  §3 THE REPO ITSELF: no dated card may carry a `generated_at` later
     than its own first kickoff. ⛔ The eleven already-damaged files are
     listed by name and the list may only SHRINK — it is the damage this
     fix ended, not a tolerance.

# @vacuity 🔴 a card rewritten after its slate started is caught
#   file: card_fb.py
#   find:     frozen, why = _frozen(path, now)
#   with:     frozen, why = (False, "")
#
# @vacuity ⛔ an unreadable published card is not an editable one
#   file: card_fb.py
#   find:         return True, ("it is already published and could not be read "
#   with:         return False, ("it is already published and could not be read "
"""
import datetime
import glob
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section
import card_fb

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 9, 18, 15, 52, tzinfo=UTC)


def stamp(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def card(date, kick, marker):
    return {"date": date, "league": "nfl", "generated_at": stamp(NOW),
            "marker": marker,
            "picks": [{"player": "A", "commence": stamp(kick)}],
            "game_lines": [{"game": "X @ Y", "commence": stamp(kick)}]}


D = tempfile.mkdtemp(prefix="frozen-")

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 DRIVEN AGAINST REAL BYTES, BOTH WAYS")
# ══════════════════════════════════════════════════════════════════════
# ⛔ NOT "does the function return False" — does the FILE change. A guard
#    that returns the right answer and writes anyway is the shape this
#    repo has shipped before.
ahead = os.path.join(D, "fb-nfl-2026-09-20.json")
published = card("2026-09-20", NOW + datetime.timedelta(hours=26), "FIRST")
io.open(ahead, "w", encoding="utf-8").write(json.dumps(published, indent=1))
before = io.open(ahead, encoding="utf-8").read()
wrote, why = card_fb.publish_dated(
    ahead, card("2026-09-20", NOW + datetime.timedelta(hours=26), "SECOND"),
    now=NOW)
after = io.open(ahead, encoding="utf-8").read()
ck("✅ a card whose slate has NOT started is rewritten normally",
   wrote and json.loads(after)["marker"] == "SECOND",
   "⛔ THE REGRESSION CHECK, AND IT COMES FIRST. Football rebuilds its "
   "card many times a day before kickoff and every one of those is "
   "correct. A freeze that stops them has broken the product. "
   "wrote=%r why=%r" % (wrote, why))

started = os.path.join(D, "fb-nfl-2026-09-17.json")
orig = card("2026-09-17", NOW - datetime.timedelta(hours=15, minutes=37),
            "PUBLISHED")
io.open(started, "w", encoding="utf-8").write(json.dumps(orig, indent=1))
before = io.open(started, encoding="utf-8").read()
wrote, why = card_fb.publish_dated(
    started, card("2026-09-17", NOW + datetime.timedelta(days=2), "OVERWRITE"),
    now=NOW)
after = io.open(started, encoding="utf-8").read()
ck("🔴🔴 a card whose first kickoff has passed is NOT rewritten",
   (not wrote) and after == before,
   "⛔ this is `picks/fb-nfl-2026-09-17.json` exactly: kickoff 00:15Z on "
   "the 18th, rewritten 15:52Z on the 18th with the NEXT week's lines. "
   "wrote=%r why=%r" % (wrote, why))
ck("⚠️ ...and the refusal says which kickoff and when, not just 'frozen'",
   "first kickoff" in why and "2026-09-18T00:15Z" in why,
   "⛔ a refusal a reader cannot check is a refusal they will delete. "
   "got %r" % (why,))
ck("⛔ ...and the published bytes are byte-identical, not merely similar",
   json.loads(after)["marker"] == "PUBLISHED",
   "got %r" % (json.loads(after).get("marker"),))

fresh = os.path.join(D, "fb-nfl-2026-09-27.json")
wrote, why = card_fb.publish_dated(fresh, card(
    "2026-09-27", NOW + datetime.timedelta(days=9), "NEW"), now=NOW)
ck("✅ a slate published for the FIRST time is always written",
   wrote and os.path.exists(fresh),
   "⛔ a freeze that blocks a brand-new slate has killed the product. "
   "wrote=%r why=%r" % (wrote, why))

# ══════════════════════════════════════════════════════════════════════
section("2. THE DECISION, ON EVERY BRANCH — INCLUDING 'CANNOT TELL'")
# ══════════════════════════════════════════════════════════════════════
ck("an unpublished path is not frozen",
   card_fb._frozen(os.path.join(D, "nope.json"), NOW)[0] is False)

bad = os.path.join(D, "corrupt.json")
io.open(bad, "w", encoding="utf-8").write("{not json")
_f, _w = card_fb._frozen(bad, NOW)
ck("🔴 an UNREADABLE published card is frozen, not editable",
   _f,
   "⛔ an absence read as permission is this project's oldest recurring "
   "error. A file we cannot parse is a file whose slate we cannot date, "
   "and overwriting it destroys the only copy. got %r" % (_w,))

nokick = os.path.join(D, "nokick-old.json")
io.open(nokick, "w", encoding="utf-8").write(json.dumps(
    {"date": "2026-09-10", "picks": [{"player": "A"}], "game_lines": []}))
_f, _w = card_fb._frozen(nokick, NOW)
ck("🔴 no readable kickoff + a slate date behind today = frozen",
   _f and "slate date" in _w,
   "got %r %r" % (_f, _w))

nokick2 = os.path.join(D, "nokick-today.json")
io.open(nokick2, "w", encoding="utf-8").write(json.dumps(
    {"date": "2026-09-27", "picks": [{"player": "A"}], "game_lines": []}))
ck("✅ ...and a FUTURE slate with no kickoff yet is still editable",
   card_fb._frozen(nokick2, NOW)[0] is False,
   "⛔ a card built before any line is priced has no commence to read "
   "and must not be frozen out of existence")

edge = os.path.join(D, "edge.json")
io.open(edge, "w", encoding="utf-8").write(json.dumps(
    card("2026-09-18", NOW, "EXACT")))
ck("⚠️ kickoff EXACTLY now counts as started",
   card_fb._frozen(edge, NOW)[0],
   "⛔ the boundary is the one place an off-by-one lives, and 'started' "
   "is the safe side of it")

# ⛔ AND THERE IS EXACTLY ONE WRITER OF A DATED CARD, so the refusal
#    cannot be bypassed by a second call site appearing later.
_src = io.open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
_writes = [l.strip() for l in _src.split("\n")
           if "json.dump(out" in l and not l.strip().startswith("#")]
ck("⛔ `card_fb.py` has exactly two `json.dump(out` sites — dated + latest",
   len(_writes) == 2,
   "🔴 a third writer would bypass the freeze entirely. found %d: %s"
   % (len(_writes), _writes))
ck("...and the dated one is inside `publish_dated()`",
   "def publish_dated" in _src
   and _src.index("def publish_dated") < _src.index("json.dump(out"),
   "the only path to the dated file has to go through the check")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 AND THE REPO ITSELF, EVERY LEAGUE, EVERY PUBLISHED CARD")
# ══════════════════════════════════════════════════════════════════════
# ⛔ THE ELEVEN ARE THE DAMAGE THIS FIX ENDED, NOT A TOLERANCE. The
#    correct content of each is gone — a published card may never be
#    edited, including to repair it — so they are listed by name and the
#    list may only SHRINK. A twelfth fails.
DAMAGED = {
    "picks/fb-ncaaf-2026-09-03.json", "picks/fb-ncaaf-2026-09-05.json",
    "picks/fb-ncaaf-2026-09-06.json", "picks/fb-ncaaf-2026-09-07.json",
    "picks/fb-ncaaf-2026-09-11.json", "picks/fb-ncaaf-2026-09-12.json",
    "picks/fb-ncaaf-2026-09-17.json", "picks/fb-nfl-2026-09-10.json",
    "picks/fb-nfl-2026-09-13.json", "picks/fb-nfl-2026-09-14.json",
    "picks/fb-nfl-2026-09-17.json",
}


def _dt(s):
    try:
        return datetime.datetime.strptime(
            s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except Exception:
        return None


late, seen, mlb = [], 0, 0
for p in sorted(glob.glob(os.path.join(ROOT, "picks", "*.json"))):
    rel = "picks/" + os.path.basename(p)
    if rel.endswith("-latest.json"):
        continue
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    gen = _dt(d.get("generated_at") or "") or _dt(d.get("built_at") or "")
    kicks = [_dt(r.get("commence") or "")
             for k in ("picks", "game_lines", "top_plays")
             for r in (d.get(k) or []) if isinstance(r, dict)]
    kicks = [k for k in kicks if k]
    if not gen or not kicks:
        continue
    seen += 1
    if "/fb-" not in rel:
        mlb += 1
    if gen > min(kicks) and rel not in DAMAGED:
        late.append("%s generated %s, first kickoff %s"
                    % (rel, gen.strftime("%m-%dT%H:%MZ"),
                       min(kicks).strftime("%m-%dT%H:%MZ")))
note("dated cards with both a stamp and a kickoff: %d (%d MLB) · "
     "known-damaged: %d" % (seen, mlb, len(DAMAGED)))
ck("🔴🔴 no card outside the known-damaged list was written after kickoff",
   not late,
   "⛔ a published estimate is what this product is judged on. %s"
   % (late,))
ck("⚠️ MLB has published cards in the sweep, so this covers every league",
   mlb >= 5,
   "⛔ a rule stated for all three leagues and measured on one is a rule "
   "measured on one. MLB cards seen: %d" % mlb)
_dead = sorted(r for r in DAMAGED
               if not os.path.exists(os.path.join(ROOT, r)))
ck("⛔ the damaged list has no dead entries — it may only shrink",
   not _dead,
   "a list nobody prunes becomes a blanket: %s" % (_dead,))
shutil.rmtree(D, ignore_errors=True)
