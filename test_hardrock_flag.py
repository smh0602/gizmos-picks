#!/usr/bin/env python3
"""THE ONE FLAG THAT REACHES THE PAGE, ON BOTH KINDS OF ROW.

🔴 `[measured 2026-09-04]` the live card carried 25 pitcher rows and 25
hitter rows. **All 8 pitcher rows Hard Rock had not posted said so. All 3
hitter rows Hard Rock had not posted said nothing** — `hitter_play()`
returned a dict with no `flags` key at all, so the branch could not exist.

⛔ THE READER SAW A DRAFTKINGS PRICE ON A HARD ROCK BOARD, unwarned, on
the book Sam actually bets. `on_hardrock` was correct the whole time — the
FIELD was right and the SENTENCE was missing, which is why only a check
that reconciles the flag against the stored board found it. A check on the
field alone is still green today.

✅ THIS FILE PINS THE BEHAVIOUR AT THE BUILDER, not on a card on disk. A
test that read `picks/<today>.json` would assert on an artifact this very
commit has not rebuilt yet, and would fail on the commit that fixes it.

⚠️ No network. Every input is constructed.
"""
import os
import sys

os.environ.setdefault("LEAGUE", "mlb")
import card as K

fails = []


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<58} {detail}")
    if not cond:
        fails.append(label)


def eq(got, want, label):
    ck(got == want, label, f"{got!r}")
    if got != want and fails and fails[-1] == label:
        fails[-1] = f"{label} (got {got!r} want {want!r})"


GAME = {"id": "g1", "away": "Cincinnati Reds", "home": "Chicago Cubs",
        "commence": "2026-09-04T23:11:00Z"}
IDS = {"Cincinnati Reds": 113, "Chicago Cubs": 112}
TEAMGAMES = {"Cincinnati Reds": 140}


def prop(hr_price):
    """One hitter prop. `hr_price=None` means Hard Rock did not post it."""
    return {
        "player": "Edwin Arroyo", "pid": 695490, "team": "Cincinnati Reds",
        "market": "batter_rbis", "side": "under", "line": 0.5,
        "price": -390, "book": "draftkings", "implied": 78.0,
        "hr": ({} if hr_price is None else
               {"price": -260, "book": "hardrockbet", "link": None}),
        "evidence": {"season": "110/130", "last15": "12/15", "home": "55/65",
                     "road": "55/65", "vs_opp": "8/9", "opp": "Chicago Cubs",
                     "bats": "S"},
    }


def hr_flags(row):
    """The flags that would actually reach the page, and no others."""
    return [f for f in (row.get("flags") or [])
            if f.get("actionable") and "Hard Rock" in (f.get("text") or "")]


print("\n1. 🔴 HARD ROCK DID NOT POST IT -> THE ROW SAYS SO")
r_off = K.hitter_play(prop(None), GAME, IDS, TEAMGAMES, hlogs={}, today="2026-09-04")
ck(isinstance(r_off, dict), "the row was built at all", type(r_off).__name__)
eq(r_off.get("on_hardrock"), False, "  on_hardrock is False")
eq(len(hr_flags(r_off)), 1, "  🔴 exactly one actionable Hard Rock flag")
# ⚠️ Guarded on purpose. When this regresses, the FAILURE above is the
# diagnosis; a traceback three lines later is noise on top of it.
_t = (hr_flags(r_off) or [{}])[0].get("text") or ""
ck("DraftKings" in _t, "  and it NAMES the book the price came from", _t[-60:])
ck("flags" in r_off, "⛔ the row HAS a flags key — it had none at all before")

print("\n2. HARD ROCK POSTED IT -> NO FLAG, AND HARD ROCK'S OWN PRICE")
r_on = K.hitter_play(prop(-260), GAME, IDS, TEAMGAMES, hlogs={}, today="2026-09-04")
eq(r_on.get("on_hardrock"), True, "on_hardrock is True")
eq(len(hr_flags(r_on)), 0, "  ⛔ no flag — a FALSE warning is a defect too")
eq(r_on.get("price"), -260, "  and the price shown is Hard Rock's own")
eq(r_on.get("book"), "hardrockbet", "  from Hard Rock")

print("\n3. THE FIELD AND THE SENTENCE CANNOT DISAGREE")
print("   ⛔ This is the pairing the live bug broke: the field was right")
print("   and the sentence was missing. Neither alone is the check.")
for _hr, _lbl in ((None, "not posted"), (-260, "posted")):
    _r = K.hitter_play(prop(_hr), GAME, IDS, TEAMGAMES, hlogs={}, today="2026-09-04")
    ck(bool(_r["on_hardrock"]) == (len(hr_flags(_r)) == 0),
       f"   {_lbl}: field and flag agree",
       f"on_hardrock={_r['on_hardrock']} flags={len(hr_flags(_r))}")

print("\n4. THE HITTER ROW MATCHES THE PITCHER ROW'S SHAPE")
print("   index.html filters on `actionable`; a differently-shaped flag")
print("   would be stored and never rendered — the same invisible failure.")
_f = (hr_flags(r_off) or [{}])[0]
for _k, _v in (("kind", "note"), ("test", "STEP 5"), ("actionable", True)):
    eq(_f.get(_k), _v, f"   flag.{_k}")

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ the Hard Rock flag is written on hitter rows, both directions")
